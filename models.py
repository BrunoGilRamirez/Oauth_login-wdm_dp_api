from typing import List

from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKeyConstraint, Index, Integer, Numeric, PrimaryKeyConstraint, Text, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.orm.base import Mapped

Base = declarative_base()


class Companies(Base):
    __tablename__ = 'companies'
    __table_args__ = (
        PrimaryKeyConstraint('id', 'name', name='companies_pkey'),
        UniqueConstraint('id', name='unique_com_id'),
        {'schema': 'private'}
    )

    id = mapped_column(BigInteger, nullable=False)
    name = mapped_column(Text, nullable=False)
    phone_number = mapped_column(Numeric(10, 0), nullable=False)
    registry = mapped_column(Date, nullable=False)
    email = mapped_column(Text)

    users: Mapped[List['Users']] = relationship('Users', uselist=True, back_populates='companies')


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = (
        ForeignKeyConstraint(['employer'], ['private.companies.id'], name='employer_fk'),
        PrimaryKeyConstraint('id', 'employer', name='users_pkey'),
        UniqueConstraint('email', name='email_unique'),
        UniqueConstraint('id', name='id_unique'),
        Index('fki_employer_fk', 'employer'),
        {'schema': 'private'}
    )

    id = mapped_column(Integer, nullable=False)
    name = mapped_column(Text, nullable=False)
    role = mapped_column(Text, nullable=False)
    email = mapped_column(Text, nullable=False)
    employer = mapped_column(Integer, nullable=False)

    companies: Mapped['Companies'] = relationship('Companies', back_populates='users')
    keys: Mapped[List['Keys']] = relationship('Keys', uselist=True, back_populates='users')


class Keys(Base):
    __tablename__ = 'keys'
    __table_args__ = (
        ForeignKeyConstraint(['owner'], ['private.users.id'], ondelete='CASCADE', onupdate='CASCADE', name='owner_fk'),
        PrimaryKeyConstraint('id', name='keys_pkey'),
        {'schema': 'private'}
    )

    id = mapped_column(BigInteger)
    owner = mapped_column(Integer, nullable=False)
    value = mapped_column(Text, nullable=False)
    registry = mapped_column(Time(True), nullable=False)
    valid_until = mapped_column(DateTime(True), nullable=False)

    users: Mapped['Users'] = relationship('Users', back_populates='keys')


class Passwords(Users):
    __tablename__ = 'passwords'
    __table_args__ = (
        ForeignKeyConstraint(['id'], ['private.users.id'], ondelete='CASCADE', onupdate='CASCADE', match='FULL', name='id_fk'),
        PrimaryKeyConstraint('id', name='passwords_pkey'),
        {'schema': 'private'}
    )

    id = mapped_column(Integer)
    value = mapped_column(Text, nullable=False)
