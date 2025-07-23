import os
from datetime import datetime

from sqlalchemy import create_engine, ForeignKey, select
from sqlalchemy import Column, Integer, String, Boolean, Date
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.orm import declarative_base
from dateutil.relativedelta import relativedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
engine = create_engine(f"sqlite:///{os.path.join(BASE_DIR, 'app.sqlite')}")

db_session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


class User(Base):
    __tablename__ = 'user'
    tg_id = Column(Integer, nullable=False, unique=True, primary_key=True)
    name = Column(String(50), nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    address = Column(String(200))
    consent_pd = Column(Boolean)
    orders = relationship("Order", back_populates="user")

    def __init__(self, tg_id, name, email, phone, address, consent_pd=None):
        self.tg_id = tg_id
        self.name = name
        self.email = email
        self.phone = phone
        self.address = address
        self.consent_pd = consent_pd

    def __repr__(self):
        return f'<info {self.tg_id} {self.name} {self.email} {self.phone} {self.consent_pd} {self.address}>'

    def create(self):
        db_session.add(self)
        db_session.commit()

    @classmethod
    def check_pd(cls, tg_id):
        try:
            return db_session.get(cls, tg_id).consent_pd
        except AttributeError:
            return None


class BocksVolume(Base):
    __tablename__ = 'box_volume'
    id = Column(Integer, primary_key=True)
    volume = Column(Integer, nullable=False, unique=True)
    orders = relationship("Order", back_populates="volume")

    def __init__(self, volume):
        self.volume = volume

    def __repr__(self):
        return f'<info {self.volume} >'

    def create(self):
        db_session.add(self)
        db_session.commit()


class Order(Base):
    __tablename__ = 'order'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.tg_id'))
    user = relationship("User", back_populates="orders")
    taking_it_myself = Column(Boolean, nullable=False)
    calling_things = Column(Boolean, nullable=False)
    volume_id = Column(Integer, ForeignKey('box_volume.id'))
    volume = relationship("BocksVolume", back_populates="orders")
    payment = Column(Boolean, nullable=False)
    rent_start = Column(Date, nullable=False)
    rent_end = Column(Date, nullable=False)
    warehouse_id = Column(Integer, ForeignKey('warehouse.id'))
    warehouse = relationship("Warehouse", back_populates="orders")
    address_from = Column(String(50))

    def __init__(self, user_id, taking_it_myself, calling_things, volume_id, warehouse_id, payment, rent_start,
                 rent_end,
                 address_from=None):
        self.user_id = user_id
        self.taking_it_myself = taking_it_myself
        self.calling_things = calling_things
        self.volume_id = volume_id
        self.payment = payment
        self.rent_start = rent_start
        self.rent_end = rent_end
        self.address_from = address_from
        self.warehouse_id = warehouse_id

    def create(self):
        db_session.add(self)
        db_session.commit()


class Warehouse(Base):
    __tablename__ = 'warehouse'
    id = Column(Integer, primary_key=True)
    address = Column(String(200), nullable=False)
    total_volume = Column(Integer, nullable=False)
    filled_volume = Column(Integer, nullable=False, default=0)
    orders = relationship("Order", back_populates="warehouse")

    def __init__(self, address, total_volume, filled_volume=0):
        self.address = address
        self.total_volume = total_volume
        self.filled_volume = filled_volume

    def create(self):
        db_session.add(self)
        db_session.commit()

    @classmethod
    def update_filling(cls, wh_id, volume):
        warehouse = db_session.get(cls, wh_id)
        warehouse.filled_volume = warehouse.filled_volume + volume

        if warehouse.filled_volume <= warehouse.total_volume:
            db_session.commit()
        else:
            raise Exception(f"Склад по адресу: {warehouse.address} - переполнен")


if __name__ == "__main__":
    # Создает базу данных
    Base.metadata.create_all(bind=engine)

    #Создаем тестовые данные
    User(123, "Тестовый пользователь", "test@test.ru", "123456", "tefwfw", 1).create()
    BocksVolume(volume=3).create()
    BocksVolume(volume=5).create()
    BocksVolume(volume=10).create()
    Warehouse(address="г. Москва, улица свободы 6", total_volume=1000).create()
    Warehouse(address="г. Санкт-Петербург, улица ленина 10", total_volume=1500).create()
    Warehouse(address="г. Москва, улица ленина 16", total_volume=2000).create()
    date_start = datetime.strptime("23.07.2025", "%d.%m.%Y").date()
    Order(user_id=123, calling_things=0, taking_it_myself=1, volume_id=1, warehouse_id=1, payment=0,
          rent_start=date_start,
          rent_end=date_start + relativedelta(months=6)
          ).create()
    db_session.commit()

