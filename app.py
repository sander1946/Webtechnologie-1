from Project import app, db
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, login_required, logout_user, current_user
from random import randint, choice
from Project.models import User, bungalow_data, bungalow_types, booking_data, populate
from Project.forms import loginForm, registerForm, resetRequestForm, resetForm, boekForm, wijzigForm, annuleerForm
import datetime


@app.route('/', methods=["GET"])
def index():
    return render_template("home.html")


@app.route('/feedback', methods=["POST"])
def feedback():
    if request.method == "POST":
        flash(f"Het bericht is verzonden!")
        print(request.args.get("email"))
        print(request.args.get("message"))
        next_page = request.args.get("next")
        if next_page is not None:
            return redirect(next_page)
    return redirect(url_for("index"))


@app.route('/logout', methods=["GET"])
@login_required
def logout():
    logout_user()
    flash('Je bent nu uitgelogd!', 'info')
    return redirect(url_for('index'))


@app.route('/login', methods=["GET", "POST"])
def login():
    form = loginForm()
    if form.validate_on_submit():
        if form.email.data != "" and form.wachtwoord.data != "":
            # Grab the user from our User Models table
            user = User.query.filter_by(email=form.email.data).first()
            if user is None:
                flash(f"De email en/of wachtwoord is incorrect! "
                      f"Vraag een nieuw wachtwoord aan als je deze bent vergeten!", "error")
                return redirect(url_for("login"))
            if user.check_password(form.wachtwoord.data) and user is not None:
                login_user(user, remember=form.remember.data)
                flash(f"Succesvol ingelogd!", "info")
                # If a user was trying to visit a page that requires a login,
                # flask saves that URL as 'next'.
                next_page = request.args.get('next')

                # So let's now check if that next exists, otherwise we'll go to
                # the welcome page.
                if next_page is None or not next_page[0] == '/':
                    next_page = url_for('bungalows')
                return redirect(next_page)
            else:
                flash(f"De email en/of wachtwoord is incorrect! "
                      f"Vraag een nieuw wachtwoord aan als je deze bent vergeten!", "error")
                return redirect(url_for("login"))
        else:
            flash("Vul een geldig e-mailadres en wachtwoord in!", "error")
            return redirect(url_for("login"))
    else:
        return render_template("auth/login.html", form=form)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = registerForm()
    if form.validate_on_submit():
        if (form.email.data != "" and form.wachtwoord.data != "" and form.voornaam.data != ""
                and form.achternaam.data != "" and form.telefoon.data != ""):
            user = User.query.filter_by(email=form.email.data)
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
                flash("Deze email is al geregistreerd! Log in plaats daarvan in!", "error")
                return redirect(url_for("login"))
        else:
            flash("Alle gegevens moeten in gevuld zijn!", "error")
            return redirect(url_for("register"))
    else:
        return render_template("auth/register.html", form=form)


@app.route('/reset_password', methods=["GET", "POST"])
def reset_password():
    form = resetRequestForm()
    if form.is_submitted():
        form.validate()
        if form.email.data != "":
            user = User.query.filter_by(email=form.email.data)
            if not user.all():
                flash(f"Dit email heeft geen nog geen account, maak er een aan!", "error")
                return redirect(url_for("register"))
            if user.first():
                link = f"/reset_password/{user.first().id}"
                flash(f'Wachtwoord reset voor het account: {form.email.data} is aangevraagd.\n'
                      f'De link is: ', link)
                return redirect(url_for("reset_password"))
        else:
            flash("Vul een geldig email en wachtwoord in!", "error")
            return redirect(url_for("reset_password"))
    return render_template("auth/reset_password_request.html", form=form)


@app.route('/reset_password/<token>', methods=["GET", "POST"])
def reset_password_token(token):
    form = resetForm()
    user = User.query.filter_by(id=token)
    if user.all():
        if form.validate_on_submit():
            if form.password.data == form.rep_password.data:
                user = User.query.get(token)
                user.change_password(form.password.data)
                db.session.add(user)
                db.session.commit()
                flash("Wachtwoord succesvol gereset!", "info")
                return redirect(url_for("login"))
            else:
                flash("De wachtwoorden komen niet overeen!", "error")
                return redirect(url_for("reset_password"))
        return render_template("auth/reset_password.html", form=form)
    else:
        flash("Ongeldige link!", "error")
        return redirect(url_for("reset_password"))


@app.route('/boek', methods=["GET"])
@login_required
def boek_inv():
    return redirect(url_for("bungalows"))


@app.route('/boek/<token>', methods=["GET", "POST"])
@login_required
def boek(token):
    form = boekForm(week=datetime.date.today().isocalendar().week)
    bungalow = []
    bungalows_info = (db.session.query(bungalow_data, bungalow_types).join(bungalow_types)
                      .filter(bungalow_data.id == token).first())
    if bungalows_info:
        data, types = bungalows_info
        bungalow_info = {"img": "/static/img/stock.png", "title": data.naam, "prijs": types.prijs,
                         "aantal_pers": types.aantal, "grote": randint(types.aantal * 45, types.aantal * 55),
                         "opmerking": choice(["Knus", "Sfeervol", "Comfortabel", "Rustiek", "Modern", "Landelijk",
                                              "Praktisch", "Gezellig", "Stijlvol", "Duurzaam"]), "id": data.id}
        bungalow.append(bungalow_info)
        if form.validate_on_submit():
            week = form.week.data
            user_id = current_user.id
            geboekt = booking_data(user_id, token, week)
            db.session.add(geboekt)
            db.session.commit()
            flash(f"Bungalow '{data.naam}' is geboekt voor week {week}")
            return redirect(url_for("boekingen"))
        return render_template("booking/boek.html", bungalow_data=bungalow, form=form,
                               week=datetime.date.today().isocalendar().week)
    else:
        return redirect(url_for("bungalows"))


@app.route('/boekingen', methods=["GET"])
@login_required
def boekingen():
    bungalow = []
    booking_info = (db.session.query(booking_data, bungalow_data, bungalow_types).select_from(booking_data).
                    join(bungalow_types, booking_data.bungalow_id == bungalow_data.id)
                    .join(bungalow_data, bungalow_data.type_id == bungalow_types.id)
                    .filter(booking_data.gast_id == current_user.id).order_by(booking_data.week.asc()).all())
    if booking_info:
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
        return render_template("booking/boekingen.html")


@app.route('/wijzig', methods=["GET"])
@login_required
def wijzig_inv():
    return redirect(url_for("boekingen"))


@app.route('/wijzig/<bungalow>', methods=["GET"])
@login_required
def wijzig_inv_inv():
    return redirect(url_for("boekingen"))


@app.route('/wijzig/<bungalow>/<token>', methods=["GET", "POST"])
@login_required
def wijzig(bungalow, token):
    form = wijzigForm(week=datetime.date.today().isocalendar().week)
    bungalow = []
    booking_info = (db.session.query(booking_data, bungalow_data, bungalow_types).select_from(booking_data).
                    join(bungalow_types, booking_data.bungalow_id == bungalow_data.id)
                    .join(bungalow_data, bungalow_data.type_id == bungalow_types.id).filter(booking_data.id == token)
                    .first())
    if booking_info:
        bookings, data, types = booking_info
        bungalow_info = {"img": "/static/img/stock.png", "title": data.naam, "prijs": types.prijs,
                         "aantal_pers": types.aantal, "grote": randint(types.aantal * 45, types.aantal * 55),
                         "opmerking": choice(["Knus", "Sfeervol", "Comfortabel", "Rustiek", "Modern", "Landelijk",
                                              "Praktisch", "Gezellig", "Stijlvol", "Duurzaam"]), "id": data.id,
                         "week": bookings.week}
        bungalow.append(bungalow_info)
        if form.validate_on_submit():
            week = form.week.data
            if week == "annuleer boeking":
                flash(f"Boeking van bungalow '{data.naam}' is geannuleerd voor week {week}")
                boeking_new = booking_data.query.get(token)
                db.session.delete(boeking_new)
                db.session.commit()
                return redirect(url_for("boekingen"))
            else:
                boeking_new = booking_data.query.get(token)
                boeking_new.week = week
                db.session.add(boeking_new)
                db.session.commit()
                flash(f"Bungalow: '{data.naam}' geboekt voor week: {week} door: {current_user.email}")
                return redirect(url_for("boekingen"))
        return render_template("booking/wijzig.html", bungalow_data=bungalow, form=form,
                               week=datetime.date.today().isocalendar().week)
    else:
        return render_template("booking/wijzig.html")


@app.route('/annuleer', methods=["GET"])
@login_required
def annuleer_inv():
    return redirect(url_for("boekingen"))


@app.route('/annuleer/<bungalow>', methods=["GET"])
@login_required
def annuleer_inv_inv():
    return redirect(url_for("boekingen"))


@app.route('/annuleer/<bungalow>/<token>', methods=["GET", "POST"])
@login_required
def annuleer(bungalow, token):
    form = annuleerForm()
    bungalow = []
    booking_info = (db.session.query(booking_data, bungalow_data, bungalow_types).select_from(booking_data).
                    join(bungalow_types, booking_data.bungalow_id == bungalow_data.id)
                    .join(bungalow_data, bungalow_data.type_id == bungalow_types.id).filter(booking_data.id == token)
                    .first())
    if booking_info:
        bookings, data, types = booking_info
        bungalow_info = {"img": "/static/img/stock.png", "title": data.naam, "prijs": types.prijs,
                         "aantal_pers": types.aantal, "grote": randint(types.aantal * 45, types.aantal * 55),
                         "opmerking": choice(["Knus", "Sfeervol", "Comfortabel", "Rustiek", "Modern", "Landelijk",
                                              "Praktisch", "Gezellig", "Stijlvol", "Duurzaam"]), "id": data.id,
                         "week": bookings.week}
        bungalow.append(bungalow_info)
        if form.validate_on_submit():
            confirm = form.confirm.data
            if confirm == "Ja":
                flash(f"Boeking van bungalow '{data.naam}' is geannuleerd voor week {bookings.week}")
                boeking_new = booking_data.query.get(token)
                db.session.delete(boeking_new)
                db.session.commit()
                return redirect(url_for("boekingen"))
            else:
                flash(f"Bungalow: '{data.naam}' is niet geannuleerd!", "info")
                return redirect(url_for("boekingen"))
        return render_template("booking/annuleer.html", bungalow_data=bungalow, form=form,
                               week=datetime.date.today().isocalendar().week)
    else:
        return render_template("booking/annuleer.html")


@app.route('/bungalows', methods=["GET"])
def bungalows():
    bungalow_lijst = []
    bungalow = db.session.query(bungalow_data, bungalow_types).join(bungalow_types).all()
    if not bungalow:
        # vul de database als deze leeg is
        populate()
        flash("De database is weer gevuld, herlaad de pagina als je niks ziet!", "error")
        redirect(url_for("bungalows"))
    for data, types in bungalow:
        bungalow_dat = {"img": "/static/img/stock.png", "title": data.naam, "prijs": types.prijs,
                        "aantal_pers": types.aantal, "grote": randint(types.aantal * 45, types.aantal * 55),
                        "opmerking": choice(["Knus", "Sfeervol", "Comfortabel", "Rustiek", "Modern", "Landelijk",
                                             "Praktisch", "Gezellig", "Stijlvol", "Duurzaam"]), "id": data.id}
        bungalow_lijst.append(bungalow_dat)
    return render_template("booking/bungalows.html", bungalow_data=bungalow_lijst)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=80, debug=True)
