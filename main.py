from flask import Flask, render_template, request, redirect, session
from sqlalchemy import create_engine, Column, String, Integer, Float, MetaData, Table, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Database connection
engine = create_engine('sqlite:///customer.db')
Session = sessionmaker(bind=engine)
db_session = Session()

Base = declarative_base()


class User(Base):
  __tablename__ = 'users'

  id = Column(Integer, primary_key=True)
  name = Column(String(100), nullable=False)
  email = Column(String(100), unique=True, nullable=False)
  password = Column(String(100), nullable=False)


class Customer(Base):
  __tablename__ = 'customers'

  id = Column(Integer, primary_key=True)
  name = Column(String(100), nullable=False)
  phone = Column(String(20), nullable=False)
  email = Column(String(100), nullable=False)
  account_number = Column(String(20), nullable=False)
  debt_balance = Column(Float, nullable=False)


metadata = MetaData()

customer_table = Table('customers', metadata,
                       Column('id', Integer, primary_key=True),
                       Column('name', String(100), nullable=False),
                       Column('phone', String(20), nullable=False),
                       Column('email', String(100), nullable=False),
                       Column('account_number', String(20), nullable=False),
                       Column('debt_balance', Float, nullable=False))

payments_table = Table(
  'payments', metadata, Column('id', Integer, primary_key=True),
  Column('customer_id', Integer, ForeignKey('customers.id'), nullable=False),
  Column('amount', Float, nullable=False),
  Column('date', DateTime, default=datetime.utcnow, nullable=False))

metadata.create_all(engine)


@app.route('/register', methods=['GET', 'POST'])
def register():
  if request.method == 'POST':
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']

    # Create a new user object
    new_user = User(name=name, email=email, password=password)

    # Add the new user to the session and commit to the database
    db_session.add(new_user)
    db_session.commit()

    # Redirect to a success page or login page
    return redirect('/login')

  return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    email = request.form['email']
    password = request.form['password']

    # Query the database for the user with the given email
    user = db_session.query(User).filter_by(email=email).first()

    if user and user.password == password:
      # User found and password matched, set session variable
      session['user_id'] = user.id

      # Redirect to the dashboard or a protected page
      return redirect('/dashboard')
    else:
      # Invalid credentials, show an error message
      error_message = "Invalid email or password"
      return render_template('login.html', error=error_message)

  return render_template('login.html')


def login_required(f):

  @wraps(f)
  def decorated_function(*args, **kwargs):
    if 'user_id' not in session:
      return redirect('/login')
    return f(*args, **kwargs)

  return decorated_function


@app.route('/dashboard')
@login_required
def dashboard():
  # Get the user id from the session
  user_id = session['user_id']

  # Query the database for the user with the given id
  user = db_session.query(User).get(user_id)

  return render_template('dashboard.html',
                         user=user,
                         user_id=session['user_id'])


@app.route('/payment', methods=['POST'])
@login_required
def payment():
  amount = float(request.form['amount'])

  # Query the database for the user with the given id
  user = db_session.query(User).get(session['user_id'])

  # Query the database for the customer associated with the user
  customer = db_session.query(Customer).get(user.customer_id)

  if customer:
    # Create a new payment record
    payment = payments_table.insert().values(customer_id=customer.id,
                                             amount=amount,
                                             date=datetime.utcnow())
    db_session.execute(payment)
    db_session.commit()

    # Update the customer's debt balance
    customer.debt_balance -= amount
    db_session.commit()

    return redirect('/dashboard')
  else:
    return redirect('/error')

app.run(host='0.0.0.0', port=80)