import locale
import datetime
from datetime import timedelta, timezone
from typing import Annotated, Literal, Union
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


def create_access_token(id: int, expires_delta: Optional[timedelta] = None):
    to_encode = {"sub": str(id)}
    if expires_delta:
        expire = datetime.datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(session: Session, username: str, password: str) -> Union[User, Literal[False]]:
    user = session.scalars(select(User).where(User.login == username)).one_or_none()
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


async def get_current_user(session: Annotated[Session, Depends(session)],
                           token: Annotated[str, Cookie()] = None) -> Optional[User]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )
    print(token)
    if not token:
        # raise credentials_exception
        return None
    try:
        print(type(token))
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # print(payload)
        id: int = payload.get("sub")
        # print(id)
        if id is None:
            # raise credentials_exception
            return None
    except JWTError as e:
        # raise credentials_exception
        print(e)
        return None
    user = session.get(User, id, options=(joinedload('*'),))
    # if user is None:
    #     # raise credentials_exception
    #     return None
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
        return RedirectResponse(request.url_for('auth'), status_code=status.HTTP_302_FOUND)
    access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        id=user.id, expires_delta=access_token_expires
    )
    resp = RedirectResponse(request.url_for('profile'), status_code=status.HTTP_302_FOUND)
    resp.set_cookie(key="token", value=access_token)
    return resp


@app.get("/", response_class=HTMLResponse)
def index(request: Request, session: Annotated[Session, Depends(session)],
          user: Annotated[Optional[User], Depends(get_current_user)] = None):
    profs = session.scalars(select(Profession))
    return templates.TemplateResponse(request, "index.html", {"profs": profs, "user": user})


@app.get("/auth")
def auth(request: Request, session: Annotated[Session, Depends(session)],
         user: Annotated[Optional[User], Depends(get_current_user)] = None):
    if user:
        return RedirectResponse(request.url_for('profile'), status_code=status.HTTP_302_FOUND)
    else:
        return templates.TemplateResponse(request, "auth.html")


@app.get("/reg", response_class=HTMLResponse)
def reg(request: Request, session: Annotated[Session, Depends(session)], email: Optional[str] = None,
        error: Optional[str] = None, user: Annotated[Optional[User], Depends(get_current_user)] = None):
    return templates.TemplateResponse(request, "reg.html", {"email": email, "user": user, "error": error})


@app.post("/reg_form", response_class=RedirectResponse)
def reg_form(session: Annotated[Session, Depends(session)], request: Request,
             login: Annotated[str, Form()],
             password: Annotated[str, Form()],
             password2: Annotated[str, Form()],
             fio: Annotated[str, Form()],
             phone: Annotated[str, Form()],
             stat: Annotated[bool, Form()] = False,
             birthdate: Annotated[Optional[datetime.date], Form()] = None,
             exp: Annotated[Optional[int], Form()] = None,
             salary: Annotated[Optional[int], Form()] = None,
             address: Annotated[Optional[str], Form()] = None
             ):
    if len(session.scalars(select(User).where(User.login == login)).all()) > 0:
        return RedirectResponse("/reg?error=Пользователь с таким логином уже существует&error_field=login", status_code=status.HTTP_302_FOUND)
    if password2 != password:
        return RedirectResponse("/reg?error=Пароли не совпадают&error_field=password")
    if birthdate > datetime.date.today():
        return RedirectResponse("/reg?error=Укажите дату в прошлом&error_field=birthdate")
    if exp < 0:
        return RedirectResponse("/reg?error=Опыт не может быть отрицательным&error_field=exp")
    if salary < 0:
        return RedirectResponse("/reg?error=Зарплата не может быть отрицательно&error_field=salary")

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

    resp = RedirectResponse(request.url_for('profile'), status_code=status.HTTP_302_FOUND)
    resp.set_cookie(key="token", value=create_access_token(user.id))
    return resp


@app.post("/vacancies", response_class=HTMLResponse)
def vacancies(request: Request, session: Annotated[Session, Depends(session)],
              prof: Annotated[Optional[int], Form()] = None, exp: Annotated[Optional[int], Form()] = None,
              salary: Annotated[Optional[int], Form()] = None,
              user: Annotated[Optional[User], Depends(get_current_user)] = None):
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
                                       "vacancies": vacancies, "user": user})


@app.get("/vacancies", response_class=HTMLResponse)
def vacancies(request: Request, session: Annotated[Session, Depends(session)], prof: Optional[int] = None,
              salary: Optional[int] = None, exp: Optional[int] = None,
              user: Annotated[Optional[User], Depends(get_current_user)] = None):
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
                                       "vacancies": vacancies, "user": user})


@app.get("/vacancies/{prof}", response_class=HTMLResponse)
def vacancies(request: Request, session: Annotated[Session, Depends(session)], prof: Optional[int] = None,
              salary: Optional[int] = None, exp: Optional[int] = None,
              user: Annotated[Optional[User], Depends(get_current_user)] = None):
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
                                       "vacancies": vacancies, "user": user})


@app.get("/vacancy/{id}", response_class=HTMLResponse)
def vacancy(request: Request, session: Annotated[Session, Depends(session)], id: int,
            user: Annotated[Optional[User], Depends(get_current_user)] = None):
    vacancy = session.get(Vacancy, id, options=(joinedload("*"),))
    return templates.TemplateResponse(request, "card.html",
                                      {"vacancy": vacancy, "employer": vacancy.employer, "user": user})


@app.get("/company/{id}", response_class=HTMLResponse)
def company(request: Request, session: Annotated[Session, Depends(session)], id: int,
            user: Annotated[Optional[User], Depends(get_current_user)] = None):
    company = session.get(Employer, id, options=(joinedload("*"),))
    return templates.TemplateResponse(request, "company.html", {"employer": company, "user": user})


@app.get("/profile", response_class=HTMLResponse)
def profile(request: Request, session: Annotated[Session, Depends(session)],
            user: Annotated[Optional[User], Depends(get_current_user)] = None):
    return templates.TemplateResponse(request, "profile.html", {"user": user})


@app.get("/responses", response_class=HTMLResponse)
def responses(request: Request, session: Annotated[Session, Depends(session)],
              user: Annotated[User, Depends(get_current_user)],
              status: int = 0, answered: int = 0):
    statuses = session.scalars(select(Status))
    stmt = select(Response).where()
    if status != 0 and session.get(Status, status):
        stmt = stmt.where(Response.status == status)
    if answered == 1:
        stmt = stmt.where(Response.employer_response != None)
    elif answered == 2:
        stmt = stmt.where(Response.employer_response == None)
    responses = session.scalars(stmt).all()
    colors = {
        1: "success",
        2: "error",
        3: "warning",
        4: "info"
    }
    return templates.TemplateResponse(request, "responses.html", {"user": user, "responses": responses, "statuses": statuses, "colors": colors})


@app.post("/responses", response_class=HTMLResponse)
def responses(request: Request, session: Annotated[Session, Depends(session)],
              user: Annotated[User, Depends(get_current_user)],
              status: Annotated[int, Form()] = 0, answered: Annotated[int, Form()] = 0):
    statuses = session.scalars(select(Status))
    stmt = select(Response).where()
    if status != 0 and session.get(Status, status):
        stmt = stmt.where(Response.status_id == status)
    if answered == 1:
        stmt = stmt.where(Response.employer_response != None)
    elif answered == 2:
        stmt = stmt.where(Response.employer_response == None)
    responses = session.scalars(stmt).all()
    colors = {
        1: "success",
        2: "error",
        3: "warning",
        4: "info"
    }
    return templates.TemplateResponse(request, "responses.html", {"user": user, "responses": responses, "statuses": statuses, "colors": colors, "status": status, "answered": answered})


@app.post("/make_response")
def make_response(request: Request, session: Annotated[Session, Depends(session)], cover_letter: Annotated[str, Form()],
                  vacancy_id: Annotated[int, Form()], user: Annotated[User, Depends(get_current_user)]):
    session.add(Response(
        cover_letter=cover_letter,
        vacancy_id=vacancy_id,
        user_id=user.id
    ))
    session.commit()
