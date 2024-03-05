from Project import app, db
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, login_required, logout_user, current_user
from random import randint, choice
from Project.models import User, BungalowData, BungalowTypes, BookingData, populate
from Project.forms import LoginForm, RegisterForm, ResetRequestForm, ResetForm, BoekForm, WijzigForm, AnnuleerForm, WijzigBungalowForm
import datetime


@app.route('/', methods=["GET"])
def index():
    """Deze functie wordt aangeroepen als de user naar de home pagina gaat"""
    return render_template("home.html")


@app.route('/feedback', methods=["POST"])
def feedback():
    """ Deze functie wordt aangeroepen als de user feedback geeft, stuur een flash message en
        stuurt de user terug naar de pagina waar ze vandaan kwamen of weer naar de home pagina"""
    if request.method == "POST":
        flash(f"Het bericht is verzonden!")
        next_page: str | None = request.args.get("next")
        if next_page is not None:
            return redirect(next_page)
    return redirect(url_for("index"))


@app.route('/logout', methods=["GET"])
@login_required
def logout():
    """Deze functie wordt aangeroepen als de user uitlogt en stuur een flash message"""
    logout_user()
    flash('Je bent nu uitgelogd!', 'info')
    return redirect(url_for('index'))


@app.route('/login', methods=["GET", "POST"])
def login():
    """Deze functie wordt aangeroepen als de user naar de login pagina gaat.
    Als de user al is ingelogd word hij naar de home pagina toe gestuurd"""
    form = LoginForm()
    # check of de user al is ingelogd
    if current_user.is_authenticated:
        flash(f"Je bent al ingelogd!", "info")
        return redirect(url_for("index"))
    # check of de form is beantwoord (POST request)
    if form.validate_on_submit():
        # check of de form is ingevuld
        if form.email.data != "" and form.wachtwoord.data != "":
            user: User = User.query.filter_by(email=form.email.data).first()
            # check of de email is geregistreerd
            if user is None:
                flash(f"De email en/of wachtwoord is incorrect! "
                      f"Vraag een nieuw wachtwoord aan als je deze bent vergeten!", "error")
                return redirect(url_for("login"))
            # check of het wachtwoord klopt
            if user.check_password(form.wachtwoord.data) and user is not None:
                login_user(user, remember=form.remember.data)
                flash(f"Succesvol ingelogd!", "info")
                # Als de user van een andere pagina komt dan de login pagina, stuur hem dan terug naar die pagina
                next_page: str | None = request.args.get('next')
                if next_page is None or not next_page[0] == '/':
                    next_page = url_for('bungalows')
                return redirect(next_page)
            else:
                # als het wachtwoord niet klopt
                flash(f"De email en/of wachtwoord is incorrect! "
                      f"Vraag een nieuw wachtwoord aan als je deze bent vergeten!", "error")
                return redirect(url_for("login"))
        else:
            # de email en/of wachtwoord niet is ingevuld
            flash("Vul een geldig e-mailadres en wachtwoord in!", "error")
            return redirect(url_for("login"))
    else:
        # als de form niet is beantwoord (GET request)
        return render_template("auth/login.html", form=form)


@app.route('/register', methods=["GET", "POST"])
def register():
    """Deze functie wordt aangeroepen als de user naar de register pagina gaat"""
    form = RegisterForm()
    # check of de form is beantwoord (POST request)
    if form.validate_on_submit():
        # check of de form is ingevuld
        if (form.email.data != "" and form.wachtwoord.data != "" and form.voornaam.data != ""
                and form.achternaam.data != "" and form.telefoon.data != ""):
            user: User = User.query.filter_by(email=form.email.data)
            # check of de email al is geregistreerd
            if not user.all():
                new_cur = User(email=form.email.data,
                               password=form.wachtwoord.data,
                               voornaam=form.voornaam.data,
                               achternaam=form.achternaam.data,
                               telefoon=form.telefoon.data)
                db.session.add(new_cur)
                db.session.commit()
                flash("Successfully registered, je kunt nu inloggen!", "info")
                return redirect(url_for("login"))
            else:
                # als de email al is geregistreerd
                flash("Deze email is al geregistreerd! Log in plaats daarvan in!", "error")
                return redirect(url_for("login"))
        else:
            # als de form niet is ingevuld
            flash("Alle gegevens moeten in gevuld zijn!", "error")
            return redirect(url_for("register"))
    else:
        # als de form niet is beantwoord (GET request)
        return render_template("auth/register.html", form=form)


@app.route('/reset_password', methods=["GET", "POST"]) # type: ignore
def reset_password():
    """Deze functie wordt aangeroepen als de user naar de reset password pagina gaat"""
    form = ResetRequestForm()
    # check of de form is beantwoord (POST request)
    if form.validate_on_submit():
        # check of de form is ingevuld
        if form.email.data != "":
            user: User = User.query.filter_by(email=form.email.data)
            if not user.all():
                # als de email niet is geregistreerd
                flash(f"Dit email heeft geen nog geen account, maak er een aan!", "error")
                return redirect(url_for("register"))
            if user.first():
                # als de email is geregistreerd
                link: str = f"/reset_password/{user.first().id}"
                flash(f'Wachtwoord reset voor het account: {form.email.data} is aangevraagd.\n'
                      f'De link is: ', link)
                return redirect(url_for("reset_password"))
        else:
            # als de form niet is ingevuld
            flash("Vul een geldig email en wachtwoord in!", "error")
            return redirect(url_for("reset_password"))
    else:
        # als de form niet is beantwoord (GET request)
        return render_template("auth/reset_password_request.html", form=form)


@app.route('/reset_password/<token>', methods=["GET", "POST"])
def reset_password_token(token: str):
    """Deze functie wordt aangeroepen als de user daadwerkelijk een wachtwoord reset link bezoekt"""	
    form = ResetForm()
    user: User = User.query.filter_by(id=token)
    # check of de token klopt
    if user.all():
        # check of de form is beantwoord (POST request)
        if form.validate_on_submit():
            if form.password.data == form.rep_password.data:
                # als de wachtwoorden overeen komen
                user = User.query.get(token)
                user.change_password(form.password.data)
                db.session.add(user)
                db.session.commit()
                flash("Wachtwoord succesvol gereset!", "info")
                return redirect(url_for("login"))
            else:
                # als de wachtwoorden niet overeen komen
                flash("De wachtwoorden komen niet overeen!", "error")
                return redirect(url_for("reset_password"))
        # als de form niet is beantwoord (GET request)
        return render_template("auth/reset_password.html", form=form)
    else:
        # als de token niet klopt
        flash("Ongeldige link!", "error")
        return redirect(url_for("reset_password"))


@app.route('/boek', methods=["GET"])
@login_required
def boek_inv():
    """Deze functie wordt aangeroepen als de user naar de boek pagina gaat zonder een bungalow te selecteren"""
    return redirect(url_for("bungalows"))


@app.route('/boek/<token>', methods=["GET", "POST"])
@login_required
def boek(token):
    """Deze functie wordt aangeroepen als de user naar de boek pagina gaat met een bungalow id in de url"""
    form = BoekForm(week=datetime.date.today().isocalendar().week)
    bungalow: list = []
    bungalows_info = (db.session.query(BungalowData, BungalowTypes).join(BungalowTypes)
                      .filter(BungalowData.id == token).first())
    # check of de bungalow id klopt
    if bungalows_info:
        data, types = bungalows_info
        bungalow_info = {"img": "/static/img/stock.png", "title": data.naam, "prijs": types.prijs,
                         "aantal_pers": types.aantal, "grote": randint(types.aantal * 45, types.aantal * 55),
                         "opmerking": choice(["Knus", "Sfeervol", "Comfortabel", "Rustiek", "Modern", "Landelijk",
                                              "Praktisch", "Gezellig", "Stijlvol", "Duurzaam"]), "id": data.id}
        bungalow.append(bungalow_info)
        if form.validate_on_submit():
            # check of de form is beantwoord (POST request)
            week: str = form.week.data
            user_id: int = current_user.id
            geboekt = BookingData(user_id, token, week)
            db.session.add(geboekt)
            db.session.commit()
            flash(f"Bungalow '{data.naam}' is geboekt voor week {week}")
            return redirect(url_for("boekingen"))
        # als de form niet is beantwoord (GET request)
        return render_template("booking/boek.html", bungalow_data=bungalow, form=form,
                               week=datetime.date.today().isocalendar().week)
    else:
        # als de bungalow id niet klopt
        return redirect(url_for("bungalows"))
    

@app.route('/boek/<bungalow>/<token>', methods=["GET", "POST"])
@login_required
def wijzigBungalow(bungalow, token):
    forms: list = []
    bungalow_lijst: list = []
    booking: BookingData = BookingData.query.filter_by(id=token).first()
    booking_data_sub = db.session.query(BookingData.bungalow_id).filter(BookingData.week == booking.week) # type: ignore
    bungalows = db.session.query(BungalowData, BungalowTypes).join(BungalowTypes).filter(BungalowData.id.notin_(booking_data_sub)).all()
    if bungalows:
        for data, types in bungalows:
            form = WijzigBungalowForm(bungalow = data.id)
            bungalow_info = {"img": "/static/img/stock.png", "title": data.naam, "prijs": types.prijs,
                                "aantal_pers": types.aantal, "grote": randint(types.aantal * 45, types.aantal * 55),
                                "opmerking": choice(["Knus", "Sfeervol", "Comfortabel", "Rustiek", "Modern", "Landelijk",
                                                    "Praktisch", "Gezellig", "Stijlvol", "Duurzaam"]), "id": data.id, "form": form}
            bungalow_lijst.append(bungalow_info)
            if form.validate_on_submit():
                # check of de form is beantwoord (POST request)
                boeking_new: BookingData = BookingData.query.get(token)
                boeking_new.bungalow_id = form.bungalow_id.data
                db.session.add(boeking_new)
                db.session.commit()
                flash(f"Bungalow: '{data.naam}' geboekt door: {current_user.email}")
                return redirect(url_for("boekingen"))
            # als de form niet is beantwoord (GET request)
    else:
        flash("Er zijn geen bungalows beschikbaar voor deze week!", "error")
        return redirect(url_for("boekingen"))

    # laat alle bungalows zien die in de database staan
    return render_template("booking/wijzigBungalow.html", bungalow_data=bungalow_lijst, forms=forms)


@app.route('/boekingen', methods=["GET"])
@login_required
def boekingen():
    """Deze functie wordt aangeroepen als de user naar de boekingen pagina gaat, en geeft de boekingen van de user weer"""
    bungalow: list = []
    booking_info = (db.session.query(BookingData, BungalowData, BungalowTypes).select_from(BookingData).
                    join(BungalowTypes, BookingData.bungalow_id == BungalowData.id)
                    .join(BungalowData, BungalowData.type_id == BungalowTypes.id)
                    .filter(BookingData.gast_id == current_user.id).order_by(BookingData.week.asc()).all())
    if booking_info:
        # check of de user boekingen heeft
        for bookings, data, types in booking_info:
            bungalow_info = {"img": "/static/img/stock.png", "title": data.naam, "prijs": types.prijs,
                             "aantal_pers": types.aantal, "grote": randint(types.aantal * 45, types.aantal * 55),
                             "opmerking": choice(["Knus", "Sfeervol", "Comfortabel", "Rustiek", "Modern", "Landelijk",
                                                  "Praktisch", "Gezellig", "Stijlvol", "Duurzaam"]), "id": data.id,
                             "week": bookings.week, "booking_id": f"{data.id}/{bookings.id}"}
            bungalow.append(bungalow_info)
        return render_template("booking/boekingen.html", bungalow_data=bungalow,
                               week=datetime.date.today().isocalendar().week)
    else:
        # als de user geen boekingen heeft
        return render_template("booking/boekingen.html")


@app.route('/wijzig', methods=["GET"])
@login_required
def wijzig_inv():
    """Deze functie wordt aangeroepen als de user naar de wijzig pagina gaat zonder een bungalow te selecteren"""
    return redirect(url_for("boekingen"))


@app.route('/wijzig/<bungalow>', methods=["GET"])
@login_required
def wijzig_inv_inv():
    """Deze functie wordt aangeroepen als de user naar de wijzig pagina gaat zonder een booking token te selecteren"""
    return redirect(url_for("boekingen"))


@app.route('/wijzig/<bungalow>/<token>', methods=["GET", "POST"])
@login_required
def wijzig(bungalow, token):
    """Deze functie wordt aangeroepen als de user naar de wijzig pagina gaat met een bungalow en booking token in de url"""
    form = WijzigForm(week=datetime.date.today().isocalendar().week)
    bungalow: list = []
    booking_info = (db.session.query(BookingData, BungalowData, BungalowTypes).select_from(BookingData).
                    join(BungalowTypes, BookingData.bungalow_id == BungalowData.id)
                    .join(BungalowData, BungalowData.type_id == BungalowTypes.id).filter(BookingData.id == token)
                    .first())
    if booking_info:
        # check of de booking token klopt
        bookings, data, types = booking_info
        bungalow_info = {"img": "/static/img/stock.png", "title": data.naam, "prijs": types.prijs,
                         "aantal_pers": types.aantal, "grote": randint(types.aantal * 45, types.aantal * 55),
                         "opmerking": choice(["Knus", "Sfeervol", "Comfortabel", "Rustiek", "Modern", "Landelijk",
                                              "Praktisch", "Gezellig", "Stijlvol", "Duurzaam"]), "id": data.id,
                         "week": bookings.week}
        bungalow.append(bungalow_info)
        if form.validate_on_submit():
            # check of de form is beantwoord (POST request)
            week: str = form.week.data
            if week == "annuleer boeking":
                # check of de user de boeking wilt annuleren
                flash(f"Boeking van bungalow '{data.naam}' is geannuleerd voor week {week}")
                boeking_new = BookingData.query.get(token)
                db.session.delete(boeking_new)
                db.session.commit()
                return redirect(url_for("boekingen"))
            else:
                # check of de user de boeking week wilt wijzigen
                boeking_new: BookingData = BookingData.query.get(token)
                boeking_new.week = week
                db.session.add(boeking_new)
                db.session.commit()
                flash(f"Bungalow: '{data.naam}' geboekt voor week: {week} door: {current_user.email}")
                return redirect(url_for("boekingen"))
        # als de form niet is beantwoord (GET request)
        return render_template("booking/wijzig.html", bungalow_data=bungalow, form=form,
                               week=datetime.date.today().isocalendar().week)
    else:
        # als de booking token niet klopt
        return render_template("booking/wijzig.html")


@app.route('/annuleer', methods=["GET"])
@login_required
def annuleer_inv():
    """Deze functie wordt aangeroepen als de user naar de annuleer pagina gaat zonder een bungalow te selecteren"""
    return redirect(url_for("boekingen"))


@app.route('/annuleer/<bungalow>', methods=["GET"])
@login_required
def annuleer_inv_inv():
    """Deze functie wordt aangeroepen als de user naar de annuleer pagina gaat zonder een booking token te selecteren"""
    return redirect(url_for("boekingen"))


@app.route('/annuleer/<bungalow>/<token>', methods=["GET", "POST"])
@login_required
def annuleer(bungalow, token):
    """Deze functie wordt aangeroepen als de user naar de annuleer pagina gaat met een bungalow en booking token in de url"""
    form = AnnuleerForm()
    bungalow: list = []
    booking_info = (db.session.query(BookingData, BungalowData, BungalowTypes).select_from(BookingData).
                    join(BungalowTypes, BookingData.bungalow_id == BungalowData.id)
                    .join(BungalowData, BungalowData.type_id == BungalowTypes.id).filter(BookingData.id == token)
                    .first())
    if booking_info:
        # check of de booking token klopt
        bookings, data, types = booking_info
        bungalow_info = {"img": "/static/img/stock.png", "title": data.naam, "prijs": types.prijs,
                         "aantal_pers": types.aantal, "grote": randint(types.aantal * 45, types.aantal * 55),
                         "opmerking": choice(["Knus", "Sfeervol", "Comfortabel", "Rustiek", "Modern", "Landelijk",
                                              "Praktisch", "Gezellig", "Stijlvol", "Duurzaam"]), "id": data.id,
                         "week": bookings.week}
        bungalow.append(bungalow_info)
        if form.validate_on_submit():
            # check of de form is beantwoord (POST request)
            confirm: str = form.confirm.data
            if confirm == "Ja":
                # check of de user de boeking wilt annuleren
                flash(f"Boeking van bungalow '{data.naam}' is geannuleerd voor week {bookings.week}")
                boeking_new = BookingData.query.get(token)
                db.session.delete(boeking_new)
                db.session.commit()
                return redirect(url_for("boekingen"))
            else:
                # check of de user de boeking wilt behouden
                flash(f"Bungalow: '{data.naam}' is niet geannuleerd!", "info")
                return redirect(url_for("boekingen"))
        # als de form niet is beantwoord (GET request)
        return render_template("booking/annuleer.html", bungalow_data=bungalow, form=form,
                               week=datetime.date.today().isocalendar().week)
    else:
        # als de booking token niet klopt
        return redirect(url_for("boekingen"))


@app.route('/bungalows', methods=["GET"])
def bungalows():
    """Deze functie wordt aangeroepen als de user naar de bungalows pagina gaat, en geeft de bungalows weer"""
    bungalow_lijst: list = []
    bungalow = db.session.query(BungalowData, BungalowTypes).join(BungalowTypes).all()
    if not bungalow:
        # check of de database leeg is (voor testen)
        populate()
        flash("De database is weer gevuld, herlaad de pagina als je niks ziet!", "error")
        redirect(url_for("bungalows"))
    for data, types in bungalow:
        bungalow_dat = {"img": "/static/img/stock.png", "title": data.naam, "prijs": types.prijs,
                        "aantal_pers": types.aantal, "grote": randint(types.aantal * 45, types.aantal * 55),
                        "opmerking": choice(["Knus", "Sfeervol", "Comfortabel", "Rustiek", "Modern", "Landelijk",
                                             "Praktisch", "Gezellig", "Stijlvol", "Duurzaam"]), "id": data.id}
        bungalow_lijst.append(bungalow_dat)
    # laat alle bungalows zien die in de database staan
    return render_template("booking/bungalows.html", bungalow_data=bungalow_lijst)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
