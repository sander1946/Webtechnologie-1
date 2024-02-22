from flask_wtf import FlaskForm
from wtforms import PasswordField, BooleanField, SubmitField, StringField, TelField, ValidationError, SelectField
from wtforms.validators import Email, Length, EqualTo, InputRequired
from Project.models import User, booking_data
from flask import request


class loginForm(FlaskForm):
    email = StringField("E-mailadres:", [InputRequired(
                       message="Dit veld is vereist"),
                       Email(
                             message="Dit is geen geldig email adres, het moet een '@' bevatten")],
                       render_kw={"placeholder": "JohnDoe@gmail.com"})
    wachtwoord = PasswordField("Wachtwoord:", [InputRequired(
                               message="Dit veld is vereist")],
                               render_kw={"placeholder": "********"})
    remember = BooleanField("Onthoud Login:", default="checked")
    submit = SubmitField("Login",
                         render_kw={"class": "btn btn-primary"})


class registerForm(FlaskForm):
    email = StringField("E-mailadres:", [InputRequired(
                       message="Dit veld is vereist"),
                       Email(
                             message="Dit is geen geldig email adres, het moet een '@' bevatten")],
                       render_kw={"placeholder": "JohnDoe@gmail.com"})
    wachtwoord = PasswordField("Wachtwoord:", [InputRequired(
                               message="Dit veld is vereist"),
                               Length(min=8, max=30,
                                      message="Wachtwoord moet tussen de 8 en 30 characters lang zijn")],
                               render_kw={"placeholder": "********"})
    rep_wachtwoord = PasswordField("Herhaal WW:", [InputRequired(
                                   message="Dit veld is vereist"),
                                   EqualTo("wachtwoord",
                                           message="Wachtwoorden moeten gelijk aan elkaar zijn")],
                                   render_kw={"placeholder": "********"})
    voornaam = StringField("Naam:", [InputRequired(
                           message="Dit veld is vereist")],
                           render_kw={"placeholder": "John"})
    achternaam = StringField([InputRequired(
                             message="Dit veld is vereist")],
                             render_kw={"placeholder": "Doe"})
    telefoon = TelField("Telefoon:", [InputRequired(
                        message="Dit veld is vereist"),
                        Length(9,
                               message="Het gegeven telefoon nummer is ongeldig")],
                        render_kw={"placeholder": "06 12345678"})
    submit = SubmitField("Registreer",
                         render_kw={"class": "btn btn-primary"})

    def check_email(self, field):
        # Check of het e-mailadres al in de database voorkomt!
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Dit e-mailadres staat al geregistreerd!')


class resetRequestForm(FlaskForm):
    email = StringField("E-mailadres:", [InputRequired(
                       message="Dit veld is vereist"),
                       Email(
                            message="Dit is geen geldig email adres, het moet een '@' bevatten")],
                       render_kw={"placeholder": "JohnDoe@gmail.com"})
    submit = SubmitField("Vraag wachtwoord reset aan",
                         render_kw={"class": "btn btn-primary"})


class resetForm(FlaskForm):
    password = PasswordField("Wachtwoord:", [InputRequired(
                             message="Dit veld is vereist"),
                             EqualTo("rep_password",
                                     message="Wachtwoorden moeten gelijk aan elkaar zijn")],
                             render_kw={"placeholder": "********"})
    rep_password = PasswordField("Wachtwoord Herhalen:", [InputRequired(
                                 message="Dit veld is vereist"),
                                 EqualTo("rep_password",
                                         message="Wachtwoorden moeten gelijk aan elkaar zijn")],
                                 render_kw={"placeholder": "********"})
    submit = SubmitField("Vraag wachtwoord reset aan", render_kw={"class": "btn btn-primary"})


class boekForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        url = request.path
        url = url.split("/")
        token = url[-1]
        data = booking_data.query.with_entities(booking_data.week).filter_by(bungalow_id=token)
        weeks = []
        for week in data:
            weeks.append(week[0])
        self.week.choices = [x for x in range(1, 53) if x not in weeks]

    week = SelectField("Welke Week?: ", [InputRequired(message="Dit veld is vereist")], coerce=int)
    submit = SubmitField("Boek Bungalow",
                         render_kw={"class": "btn btn-primary"})


class wijzigForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        url = request.path
        url = url.split("/")
        bungalow = url[-2]
        data = booking_data.query.with_entities(booking_data.week).filter_by(bungalow_id=bungalow)
        weeks = []
        for week in data:
            weeks.append(week[0])
        coises = [x for x in range(1, 53) if x not in weeks]
        coises.append("annuleer boeking")
        self.week.choices = coises

    week = SelectField("Nieuwe Week?: ", [InputRequired(message="Dit veld is vereist")], coerce=str)
    submit = SubmitField("Boek Bungalow",
                         render_kw={"class": "btn btn-primary"})
