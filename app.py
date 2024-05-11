import locale
import datetime
from datetime import timedelta, timezone
from typing import Annotated, Literal
import logging

from fastapi import FastAPI, Depends, Request, Form, HTTPException, Cookie, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqladmin import Admin as SQLAdmin
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session, joinedload

import config
from admin_auth import AdminAuth
from views import *


logging.getLogger('passlib').setLevel(logging.ERROR)

engine = create_engine(config.DB_URL)
sessionmaker = sessionmaker(engine, expire_on_commit=False)
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')


def session():
    with sessionmaker() as session:
        yield session


SECRET_KEY = "0aca94f15c5eb45e31e13c20b819619731da7a7d3989d7aca954f796544010a9"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(id: int, expires_delta: timedelta | None = None):
    to_encode = {"sub": id}
    if expires_delta:
        expire = datetime.datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(session: Session, username: str, password: str) -> User | Literal[False]:
    user = session.scalar(select(User).where(User.login == username))
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


async def get_current_user(token: Annotated[str, Cookie()] = None) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: int = payload.get("sub")
        if id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = session.get(User, id)
    if user is None:
        raise credentials_exception
    return user


class Token(BaseModel):
    access_token: str
    token_type: str


app = FastAPI()

auth_backend = AdminAuth(SECRET_KEY, sessionmaker)
admin = SQLAdmin(app, engine, authentication_backend=auth_backend, logo_url="/static/icons/favicon.svg",
                 title="DevHunter Admin")
list(map(admin.add_view, (UserView, AdminView, ResponseView, VacancyView, EmployerView, StatusView, ProfessionView)))

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="template")
templates.env.globals.setdefault("str", str)
templates.env.globals.setdefault("len", len)


@app.post("/auth_form", response_class=RedirectResponse)
def auth_form(
        request: Request,
        session: Annotated[Session, Depends(session)],
        login: Annotated[str, Form()],
        password: Annotated[str, Form()]
):
    user = authenticate_user(session, login, password)
    if not user:
        return RedirectResponse(request.url_for('auth'))
    access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        id=user.id, expires_delta=access_token_expires
    )
    resp = RedirectResponse(request.url_for('profile'))
    resp.set_cookie(key="token", value=access_token)
    return resp


@app.get("/", response_class=HTMLResponse)
def index(request: Request, session: Annotated[Session, Depends(session)]):
    profs = session.scalars(select(Profession))
    return templates.TemplateResponse(request, "index.html", {"profs": profs})


@app.get("/auth", response_class=HTMLResponse)
def auth(request: Request, session: Annotated[Session, Depends(session)]):
    return templates.TemplateResponse(request, "auth.html")


@app.get("/reg", response_class=HTMLResponse)
def reg(request: Request, session: Annotated[Session, Depends(session)], email: Optional[str] = None, error: Optional[str] = None):
    return templates.TemplateResponse(request, "reg.html", {"email": email})


@app.post("/reg_form", response_class=RedirectResponse)
def reg_form(session: Annotated[Session, Depends(session)], request: Request,
             login: Annotated[str, Form()],
             password: Annotated[str, Form()],
             fio: Annotated[str, Form()],
             phone: Annotated[str, Form()],
             stat: Annotated[bool, Form()] = False,
             birthdate: Annotated[Optional[datetime.date], Form()] = None,
             exp: Annotated[Optional[int], Form()] = None,
             salary: Annotated[Optional[int], Form()] = None,
             address: Annotated[Optional[str], Form()] = None
             ):
    if len(session.scalars(select(User).where(User.login == login)).all()) > 0:
        return RedirectResponse("/reg?error=Пользователь с таким логином уже существует")
    user = User(
        login=login,
        password=get_password_hash(password),
        name=fio,
        phone=phone,
        status=stat,
        birthdate=birthdate,
        exp=exp,
        salary=salary,
        address=address
    )
    session.add(user)
    session.commit()

    resp = RedirectResponse(request.url_for('profile'))
    resp.set_cookie(key="token", value=create_access_token(user.id))
    return resp


@app.get("/responses", response_class=HTMLResponse)
def responses(request: Request, session: Annotated[Session, Depends(session)], user: Annotated[User, Depends(get_current_user)]):
    return templates.TemplateResponse(request, "responses.html")


@app.post("/vacancies", response_class=HTMLResponse)
def vacancies(request: Request, session: Annotated[Session, Depends(session)],
              prof: Annotated[Optional[int], Form()] = None, exp: Annotated[Optional[int], Form()] = None,
              salary: Annotated[Optional[int], Form()] = None):
    profs = session.scalars(select(Profession))
    vacs = select(Vacancy)
    if prof is not None:
        vacs = vacs.where(Vacancy.profession_id == prof)
    if exp is not None:
        vacs = vacs.where(Vacancy.exp <= exp)
    if salary is not None:
        vacs = vacs.where(Vacancy.salary >= salary)
    vacs = vacs.options(joinedload('*'))
    vacancies = session.execute(vacs).unique().scalars().all()
    return templates.TemplateResponse(request, "vacancies.html",
                                      {"prof_id": prof, "exp": exp, "salary": salary, "profs": profs,
                                       "vacancies": vacancies})


@app.get("/vacancies", response_class=HTMLResponse)
def vacancies(request: Request, session: Annotated[Session, Depends(session)], prof: Optional[int] = None,
              salary: Optional[int] = None, exp: Optional[int] = None):
    profs = session.scalars(select(Profession))
    vacs = select(Vacancy)
    if prof is not None:
        vacs = vacs.where(Vacancy.profession_id == prof)
    if exp is not None:
        vacs = vacs.where(Vacancy.exp <= exp)
    if salary is not None:
        vacs = vacs.where(Vacancy.salary >= salary)
    vacs = vacs.options(joinedload('*'))
    vacancies = session.execute(vacs).unique().scalars().all()
    return templates.TemplateResponse(request, "vacancies.html",
                                      {"prof_id": prof, "exp": exp, "salary": salary, "profs": profs,
                                       "vacancies": vacancies})


@app.get("/vacancies/{prof}", response_class=HTMLResponse)
def vacancies(request: Request, session: Annotated[Session, Depends(session)], prof: Optional[int] = None,
              salary: Optional[int] = None, exp: Optional[int] = None):
    profs = session.scalars(select(Profession))
    vacs = select(Vacancy)
    if prof is not None:
        vacs = vacs.where(Vacancy.profession_id == prof)
    if exp is not None:
        vacs = vacs.where(Vacancy.exp <= exp)
    if salary is not None:
        vacs = vacs.where(Vacancy.salary >= salary)
    vacs = vacs.options(joinedload('*'))
    vacancies = session.execute(vacs).unique().scalars().all()
    return templates.TemplateResponse(request, "vacancies.html",
                                      {"prof_id": prof, "exp": exp, "salary": salary, "profs": profs,
                                       "vacancies": vacancies})


@app.get("/vacancy/{id}", response_class=HTMLResponse)
def vacancy(request: Request, session: Annotated[Session, Depends(session)], id: int):
    vacancy = session.get(Vacancy, id, options=(joinedload("*"),))
    return templates.TemplateResponse(request, "card.html", {"vacancy": vacancy, "employer": vacancy.employer})


@app.get("/company/{id}", response_class=HTMLResponse)
def company(request: Request, session: Annotated[Session, Depends(session)], id: int):
    company = session.get(Employer, id, options=(joinedload("*"),))
    return templates.TemplateResponse(request, "company.html", {"employer": company})


@app.get("/profile", response_class=HTMLResponse)
def profile(request: Request, session: Annotated[Session, Depends(session)]):
    return templates.TemplateResponse(request, "profile.html")


@app.post("/make_response")
def make_response(request: Request, session: Annotated[Session, Depends(session)], cover_letter: Annotated[str, Form()],
                  vacancy_id: Annotated[int, Form()]):
    session.add(Response(
        cover_letter=cover_letter,
        vacancy_id=vacancy_id,
        user_id=request.user.id
    ))
