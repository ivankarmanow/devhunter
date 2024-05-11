import datetime
from hashlib import sha256
from uuid import uuid4

from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import select
from sqladmin.authentication import AuthenticationBackend
from fastapi import Request
from fastapi.responses import RedirectResponse

from models.db import AdminToken, Admin


class AdminAuth(AuthenticationBackend):

    def __init__(self, secret_key: str, sessionmaker: sessionmaker):
        super().__init__(secret_key)
        self.sessionmaker = sessionmaker

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]

        with self.sessionmaker.begin() as session:
            session: Session
            admin = session.scalar(select(Admin).where(Admin.login == username))
            if not admin:
                return False
            if admin.password != sha256(password.encode()).hexdigest():
                return False
            token = str(uuid4())
            session.add(AdminToken(token=token, admin_id=admin.id, expire = datetime.datetime.now() + datetime.timedelta(days=28)))

        request.session.update({"token": token, "admin_id": admin.id})
        print("Yep")
        return True

    async def logout(self, request: Request) -> bool:
        token = request.session.get("token")
        with self.sessionmaker.begin() as session:
            session: Session
            session.delete(session.scalar(select(AdminToken).where(AdminToken.token == token)))
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:

        token = request.session.get("token")

        if not token:
            return False

        with self.sessionmaker.begin() as session:
            session: Session
            tk: AdminToken | None = session.scalar(select(AdminToken).where(AdminToken.token == token))
            if not tk:
                request.session.clear()
                return False
            if request.session.get("admin_id") != tk.admin_id:
                request.session.clear()
                return False
            if tk.expire < datetime.datetime.now():
                request.session.clear()
                return False
            tk.expire = datetime.datetime.now() + datetime.timedelta(days=28)

        return True
