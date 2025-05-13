from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_use = Column(DateTime, default=datetime.now)
    requests_count = Column(Integer, default=0)
    fav_servers = Column(String, default="{}")

class MySession:
    def __init__(self, path='sqlite:///data.sqlite'):
        engine = create_engine(path)
        Base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine)
        self.session = Session()

    def add_user(self, user):
        """Добавляет пользователя в БД"""
        try:
            self.session.add(user)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

    def add_request(self, user_id: int):
        """Добавляет запрос пользователю"""
        try:
            user = self.session.query(User).filter_by(id=user_id).one()
            user.requests_count += 1
            self.session.commit()

        except NoResultFound:
            print(f"Пользователь с id={user_id} не найден")

        except Exception as e:
            self.session.rollback()
            print(f"Ошибка при обновлении: {e}")


    def get_fav_servers(self, user_id: int) -> dict[str, str]:
        """Возвращает избранные сервера пользователя"""
        try:
            user = self.session.query(User).filter_by(id=user_id).one()
            res = json.loads(user.fav_servers)

            return res

        except NoResultFound:
            print(f"Пользователь с id={user_id} не найден")
            return {}



    def set_fav_servers(self, user_id: int, fav_servers):
        """Устонавливает избранные сервера пользователя"""
        try:
            user = self.session.query(User).filter_by(id=user_id).one()
            user.fav_servers = json.dumps(fav_servers)
            self.session.commit()

        except NoResultFound:
            print(f"Пользователь с id={user_id} не найден")
