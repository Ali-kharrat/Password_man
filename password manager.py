import sqlite3
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import scrypt
import base64
import csv


conn = sqlite3.connect('passwords.db')
c = conn.cursor()


c.execute('''CREATE TABLE IF NOT EXISTS passwords
             (id INTEGER PRIMARY KEY, website TEXT, username TEXT, encrypted_password TEXT, nonce TEXT, tag TEXT)''')

class PasswordManager:
    def __init__(self, master_password):
        self.master_password = master_password
        self.key = scrypt(self.master_password, b'salt', 32, N=2**14, r=8, p=1)
    
    def encrypt_password(self, password):
        cipher = AES.new(self.key, AES.MODE_GCM)
        ct, tag = cipher.encrypt_and_digest(password.encode())
        return base64.b64encode(ct).decode('utf-8'), base64.b64encode(cipher.nonce).decode('utf-8'), base64.b64encode(tag).decode('utf-8')
    
    def decrypt_password(self, encrypted_password, nonce, tag):
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=base64.b64decode(nonce))
        pt = cipher.decrypt_and_verify(base64.b64decode(encrypted_password), base64.b64decode(tag))
        return pt.decode('utf-8')

    def save_password_db(self, website, username, password):
        enc_password, nonce, tag = self.encrypt_password(password)
        
        if (f'{website}',) in c.execute("SELECT website FROM passwords").fetchall():
            c.execute(f"UPDATE passwords SET username = '{username}', encrypted_password = '{enc_password}', nonce = '{nonce}', tag = '{tag}' WHERE website = '{website}'")
            conn.commit()
        else:
            c.execute("INSERT INTO passwords (website, username, encrypted_password, nonce, tag) VALUES (?, ?, ?, ?, ?)", (website, username, enc_password, nonce, tag))
            conn.commit()
    
    def get_password_db(self, website):
        c.execute("SELECT * FROM passwords WHERE website=?", (website,))
        result = c.fetchone()
        print(result)

        if result:
            dec_password = self.decrypt_password(result[3], result[4], result[5])
            username = result[2]
            return dec_password , username
        else:
            return None
    def export_data(self):

        c.execute("SELECT * FROM passwords")
        rows = c.fetchall()
        csv_file = "passwords.csv"
        with open(csv_file, 'a', newline='') as file:
            csv_writer = csv.writer(file)
            csv_writer.writerow([i[0] for i in c.description])
            csv_writer.writerows(rows)

        print("Sucseccfuly")


        conn.close()
    def import_data(self,address):
        with open(address,"r") as csv:
            heading = next(csv)
            lines = csv.readlines()
            for line in lines:
                line = line.rsplit()
                print(line)
                line = line[0].split(',')
                if (f'{line[1]}',) in c.execute("SELECT website FROM passwords").fetchall():
                    c.execute(f"UPDATE passwords SET username = '{line[2]}', encrypted_password = '{line[3]}', nonce = '{line[4]}', tag = '{line[5]}' WHERE website = '{line[1]}'")
                    conn.commit()
                else:
                    c.execute("INSERT INTO passwords (website, username, encrypted_password, nonce, tag) VALUES (?, ?, ?, ?, ?)", (line[1], line[2], line[3], line[3], line[5]))
                    conn.commit()
        print("Sucseccfuly")


master_password = "@/#SaF4r1"
pm = PasswordManager(master_password)



def main():

    print("""hello welcom to password manager
          for use this app you should say what you wnat to do? (use number)
          1 - ADD new user name and password
          2 - see a your password
          3 - export all data (CSV)
          4 - import password file (CSV)""")
    command = input("what do you wnat? ")

    if command == "1":
        print("ADD New Password\n-------------------------")
        website = input("website: ")
        username = input("username: ")
        password = input("password: ")

        pm.save_password_db(website, username, password)
        conn.close()

    elif command == "2":
        website = input("website: ")

        retrieved_password = pm.get_password_db(website)
        print(f"Retrieved Password: {retrieved_password}")
        conn.close()
    
    elif command == "3":
        pm.export_data() 

    elif command == "4":
        address_file = input("address of file: ")
        pm.import_data(address_file)
    
    else:
        main()


main()

    


