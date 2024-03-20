from typing import List

from sqlalchemy import BigInteger, Column, Date, ForeignKeyConstraint, Index, Integer, Numeric, PrimaryKeyConstraint, Text, UniqueConstraint
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
        PrimaryKeyConstraint('id', 'email', 'secret', name='users_pkey'),
        UniqueConstraint('email', name='email_unique'),
        UniqueConstraint('id', name='id_unique'),
        UniqueConstraint('secret', name='secret_unique'),
        Index('fki_employer_fk', 'employer'),
        {'schema': 'private'}
    )

    id = mapped_column(Integer, nullable=False)
    name = mapped_column(Text, nullable=False)
    role = mapped_column(Text, nullable=False)
    email = mapped_column(Text, nullable=False)
    employer = mapped_column(Integer, nullable=False)
    secret = mapped_column(Text, nullable=False)

    companies: Mapped['Companies'] = relationship('Companies', back_populates='users')
    keys: Mapped[List['Keys']] = relationship('Keys', uselist=True, back_populates='users')
    passwords: Mapped['Passwords'] = relationship('Passwords', uselist=False, back_populates='users')


class Keys(Base):
    __tablename__ = 'keys'
    __table_args__ = (
        ForeignKeyConstraint(['owner'], ['private.users.secret'], ondelete='CASCADE', onupdate='CASCADE', name='owner'),
        PrimaryKeyConstraint('id', name='keys_pkey'),
        Index('fki_owner', 'owner'),
        {'schema': 'private'}
    )

    id = mapped_column(BigInteger)
    value = mapped_column(Text, nullable=False)
    valid_until = mapped_column(Date, nullable=False)
    owner = mapped_column(Text, nullable=False)
    registry = mapped_column(Date, nullable=False)

    users: Mapped['Users'] = relationship('Users', back_populates='keys')


class Passwords(Base):
    __tablename__ = 'passwords'
    __table_args__ = (
        ForeignKeyConstraint(['owner'], ['private.users.secret'], ondelete='CASCADE', onupdate='CASCADE', name='owner_fk'),
        PrimaryKeyConstraint('id', 'owner', name='passwords_pkey'),
        UniqueConstraint('id', name='id_u'),
        UniqueConstraint('owner', name='owner_unique'),
        {'schema': 'private'}
    )

    value = mapped_column(Text, nullable=False)
    id = mapped_column(Integer, nullable=False)
    owner = mapped_column(Text, nullable=False)

    users: Mapped['Users'] = relationship('Users', back_populates='passwords')
