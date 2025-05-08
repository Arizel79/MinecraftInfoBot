from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)

# Подключение к SQLite (файловая БД)
engine = create_engine('sqlite:///example.db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

# Добавление пользователя
new_user = User(name='Bob', age=30)
session.add(new_user)
session.commit()

# Получение пользователей
users = session.query(User).all()
for user in users:
    print(user.id, user.name, user.age)