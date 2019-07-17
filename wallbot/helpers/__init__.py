from .lookups import *
from .truststore import *
from .authorisation import *

# import json
#
# class Trusted(list):
#     """ Persistent trust store """
#
#     def __init__(self, filepath):
#         self.filepath = filepath
#         self.users = []
#
#         if len(self.users) >= 0:
#             self.load()
#
#     def add(self, user):
#         """ Add user to Trusted """
#         self.users.append(user)
#         self.update()
#
#     def remove(self, user):
#         """ Remove user from Trusted """
#         self.users.remove(user)
#         self.update()
#
#     def load(self):
#         """ Load data from on-disk store """
#         try:
#             with open(self.filepath, 'r') as f:
#                 self.users = json.load(f)
#         except:
#             self.users = [initial_user]
#             self.update()
#
#     def update(self):
#         """ Update on-disk store """
#         parsed = json.dumps(self.users)
#         with open(self.filepath, 'w') as f: f.write(parsed)
