import datetime
from typing import Optional

from sqlalchemy import ForeignKey, func
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import Text, JSON
from sqlalchemy.orm import relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    birthdate: Mapped[Optional[datetime.date]]
    gender: Mapped[Optional[bool]]
    reg_date: Mapped[datetime.date] = mapped_column(default=datetime.date.today)
    exp: Mapped[Optional[int]]
    cv: Mapped[Optional[str]] = mapped_column(Text)
    salary: Mapped[Optional[int]]
    phone: Mapped[str]
    status: Mapped[bool]
    contacts: Mapped[Optional[dict]] = mapped_column(JSON)
    address: Mapped[Optional[str]]
    login: Mapped[str]
    password: Mapped[str]

    responses: Mapped[list["Response"]] = relationship("Response", back_populates="user")

    def __str__(self):
        return f"{self.name} ({self.login}, {self.id})"


class Employer(Base):
    __tablename__ = 'employers'

    id: Mapped[int] = mapped_column(primary_key=True)
    company_name: Mapped[str]
    website: Mapped[Optional[str]]
    description: Mapped[Optional[str]] = mapped_column(Text)
    contacts: Mapped[Optional[dict]] = mapped_column(JSON)
    slogan: Mapped[Optional[str]]
    short_description: Mapped[Optional[str]]

    vacancies: Mapped[list["Vacancy"]] = relationship("Vacancy", back_populates="employer")

    def __str__(self):
        return f"{self.company_name} ({self.website}, {self.id})"


class Admin(Base):
    __tablename__ = 'admins'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    login: Mapped[str]
    password: Mapped[str]

    tokens: Mapped[list["AdminToken"]] = relationship("AdminToken", back_populates="admin")

    def __str__(self):
        return f"{self.name} ({self.login}, {self.id})"


class Profession(Base):
    __tablename__ = 'professions'

    id: Mapped[int] = mapped_column(primary_key=True)
    profession: Mapped[str]

    vacancies: Mapped[list["Vacancy"]] = relationship("Vacancy", back_populates="profession")

    def __str__(self):
        return f"{self.profession} ({self.id})"


class Status(Base):
    __tablename__ = 'status'

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str]

    responses: Mapped[list["Response"]] = relationship("Response", back_populates="status")

    def __str__(self):
        return f"{self.status} ({self.id})"


class Vacancy(Base):
    __tablename__ = 'vacancies'

    id: Mapped[int] = mapped_column(primary_key=True)
    salary: Mapped[Optional[int]]
    exp: Mapped[Optional[int]]
    content: Mapped[Optional[str]] = mapped_column(Text)
    short_text: Mapped[Optional[str]]
    address: Mapped[Optional[str]]
    pub_date: Mapped[datetime.datetime] = mapped_column(server_default=func.now())

    profession_id: Mapped[int] = mapped_column(ForeignKey('professions.id'))
    employer_id: Mapped[int] = mapped_column(ForeignKey('employers.id'))

    profession: Mapped["Profession"] = relationship("Profession", back_populates="vacancies")
    employer: Mapped["Employer"] = relationship("Employer", back_populates="vacancies")

    responses: Mapped[list["Response"]] = relationship("Response", back_populates="vacancy")

    def __repr__(self):
        return f"{self.profession} ({self.employer}, {self.id})"


class Response(Base):
    __tablename__ = 'responses'

    id: Mapped[int] = mapped_column(primary_key=True)
    cover_letter: Mapped[Optional[str]] = mapped_column(Text)
    response_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    employer_response: Mapped[Optional[str]] = mapped_column(Text)
    
    vacancy_id: Mapped[int] = mapped_column(ForeignKey('vacancies.id'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    status_id: Mapped[int] = mapped_column(ForeignKey('status.id'), default=3)

    vacancy: Mapped["Vacancy"] = relationship("Vacancy", back_populates="responses")
    user: Mapped["User"] = relationship("User", back_populates="responses")
    status: Mapped["Status"] = relationship("Status", back_populates="responses")

    def __str__(self):
        return f"Отклик {self.vacancy} {self.user}"


class AdminToken(Base):
    __tablename__ = "admin_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str]
    expire: Mapped[datetime.datetime]

    admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id"))

    admin: Mapped["Admin"] = relationship("Admin", back_populates="tokens")