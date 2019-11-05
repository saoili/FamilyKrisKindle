import json
import random
from getpass import getpass
from smtplib import SMTPAuthenticationError, SMTP_SSL
from ssl import create_default_context


STMP = "smtp.gmail.com"
PORT = 465  # For SSL
PASSWORD = getpass("Type your password and press enter: ")
CONFIG_FILE = "config.json"
random.seed()
# TODO make the year dynamic
# also write tests
# and a readme
# make a generic config file to upload
# probably a bunch of other stuff
MAIL_BODY = """
Hi {recipients}

This is an automated mail sent from a program Sorcha had
a bunch of fun writing.

For the 2019 Family Kris Kindle you have been assigned {assignment}
"""


def load_config():
  try:
    with open(CONFIG_FILE, 'r') as file:
      return json.loads(file.read())
  except Exception as err:
    print("Something went wrong loading the config file")
    print("You do have a file called config.json, right?")
    print(f"'Something' was {err}")
    exit()


def assign_oldies(oldies):
  have_assignee = set()
  is_assigned = set()
  assignments = {}
  for oldie in oldies:
    if len(have_assignee) == len(oldies) - 1 and {oldie} == oldies - is_assigned:
      return assign_oldies(oldies)
    chosen = oldie
    while chosen == oldie:
      chosen = random.choice(list(oldies - is_assigned))
    have_assignee.add(oldie)
    is_assigned.add(chosen)
    assignments[oldie] = chosen

  return assignments


def assign_kids(oldies_with_kids, family, kids, pressies_per):
  assignments = {}
  assigned = set()
  kids_left = kids.copy()

  for oldie in oldies_with_kids:
    their_kids = family[oldie]['kids']

    valid_kids = set(kids_left) - set(their_kids)
    if len(valid_kids) < pressies_per:
      return assign_kids(oldies_with_kids, family, kids, pressies_per)

    assignments[oldie] = []
    for i in range(pressies_per):
      chosen = their_kids[0]
      while (
        chosen in family[oldie]['kids'] or
        chosen in assignments[oldie]
      ):
        chosen = random.choice(kids_left)
      assigned.add(chosen)
      assignments[oldie].append(chosen)
      kids_left.remove(chosen)

  return assignments


def generate_assignments(config):
  # error handling here seems overboard
  family = config.get("family")
  pressies_per = config.get("pressies per")
  number_of_kids = sum([len(k) for k in [i['kids'] for i in family.values()]])
  # print(f"\nfamily is {family}\n")
  oldies_with_kids = [f for f in family if family[f]['kids']]
  oldies_without_kids = [f for f in family if not family[f]['kids']]
  # for f in family:
  #   # print(f"f is {f}")
  #   if family[f]['kids']:
  #     # print(f"yeah, {f} has kids")
  #   else:
  #     print(f"no, {f} doesn't")
  oldies = set(oldies_with_kids + oldies_without_kids)
  charities = (len(oldies_with_kids) * pressies_per) % number_of_kids
  kids = []
  for sub_family in family.values():
    for kid in sub_family['kids']:
      kids.append(kid)
      kids.append(kid)
  for i in range(charities):
    kids.append(f'charity')

  assignments = {}

  # print(f"oldies_without_kids is {oldies_without_kids}")
  odlie_assignments = assign_oldies(oldies)
  # print(f"odlie_assignments is {odlie_assignments}")
  kid_assignements = assign_kids(oldies_with_kids, family, kids, pressies_per)
  for oldie, odlie_assignment in odlie_assignments.items():
    assignments[oldie] = {
      'oldie': odlie_assignment,
      'kids': kid_assignements.get(oldie, [])
    }

  return assignments


def send_email(recipients, mail_body, sender_email):
  # Create a secure SSL context
  context = create_default_context()

  with SMTP_SSL(STMP, PORT, context=context) as server:
    try:
      server.login(sender_email, PASSWORD)
      # TODO: Send email here
    except SMTPAuthenticationError:
      print("Password wrong, try again")
      return
    server.sendmail(sender_email, recipients, mail_body)
    print(f"if we failed we did so after sending a mail to {recipients}")


def main():
  config = load_config()
  selections = generate_assignments(config)
  # print(f"selections is {selections}")
  for oldie, assignments in selections.items():
    adults = assignments.get('oldie')
    kids = ", ".join(assignments.get('kids', []))
    if kids:
      assignment = " and ".join([adults, kids])
    else:
      assignment = adults
    mail_body = MAIL_BODY.format(
      recipients=oldie, assignment=assignment)
    # print(f"would send {mail_body}")
    send_email(
      config['family'][oldie]['email addresses'],
      mail_body, config["Sender"]
    )

  # print(f"config is {config}")
  # send_email(["saoili@gmail.com", "saoili@google.com"], "test email")


if __name__ == '__main__':
  main()


