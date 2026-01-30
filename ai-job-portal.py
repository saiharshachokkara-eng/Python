import sqlite3
import hashlib
import uuid
import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class Database:
    def __init__(self, name="job_portal.db"):
        self.conn = sqlite3.connect(name)
        self.create()

    def create(self):
        c = self.conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,email TEXT UNIQUE,password TEXT,role TEXT,created TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS candidates(user_id TEXT,name TEXT,skills TEXT,experience INTEGER,resume TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,hr_id TEXT,title TEXT,description TEXT,skills TEXT,min_exp INTEGER,created TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS applications(id TEXT PRIMARY KEY,candidate_id TEXT,job_id TEXT,score REAL,applied TEXT)")
        self.conn.commit()

class Security:
    @staticmethod
    def hash(p):
        return hashlib.sha256(p.encode()).hexdigest()
    @staticmethod
    def uid():
        return str(uuid.uuid4())

class Auth:
    def __init__(self, db):
        self.db = db
    def register(self, email, password, role):
        c = self.db.conn.cursor()
        uid = Security.uid()
        c.execute("INSERT INTO users VALUES(?,?,?,?,?)",
                  (uid, email, Security.hash(password), role, str(datetime.datetime.now())))
        self.db.conn.commit()
        return uid
    def login(self, email, password):
        c = self.db.conn.cursor()
        c.execute("SELECT id,password,role FROM users WHERE email=?", (email,))
        r = c.fetchone()
        if r and Security.hash(password) == r[1]:
            return {"id": r[0], "role": r[2]}
        return None

class Candidate:
    def __init__(self, db):
        self.db = db
    def create(self, uid, name, skills, exp, resume):
        c = self.db.conn.cursor()
        c.execute("INSERT INTO candidates VALUES(?,?,?,?,?)", (uid, name, skills, exp, resume))
        self.db.conn.commit()
    def get(self, uid):
        c = self.db.conn.cursor()
        c.execute("SELECT * FROM candidates WHERE user_id=?", (uid,))
        return c.fetchone()

class Job:
    def __init__(self, db):
        self.db = db
    def post(self, hr, title, desc, skills, exp):
        jid = Security.uid()
        c = self.db.conn.cursor()
        c.execute("INSERT INTO jobs VALUES(?,?,?,?,?,?,?)",
                  (jid, hr, title, desc, skills, exp, str(datetime.datetime.now())))
        self.db.conn.commit()
        return jid
    def all(self):
        c = self.db.conn.cursor()
        c.execute("SELECT * FROM jobs")
        return c.fetchall()

class AIMatch:
    def __init__(self):
        self.v = TfidfVectorizer(stop_words="english")
    def score(self, resume, job):
        x = self.v.fit_transform([resume, job])
        return round(cosine_similarity(x[0:1], x[1:2])[0][0] * 100, 2)

class Application:
    def __init__(self, db, ai):
        self.db = db
        self.ai = ai
    def apply(self, cid, jid, resume, skills):
        s = self.ai.score(resume, skills)
        c = self.db.conn.cursor()
        c.execute("INSERT INTO applications VALUES(?,?,?,?,?)",
                  (Security.uid(), cid, jid, s, str(datetime.datetime.now())))
        self.db.conn.commit()
        return s

class CLI:
    def __init__(self):
        self.db = Database()
        self.auth = Auth(self.db)
        self.cand = Candidate(self.db)
        self.job = Job(self.db)
        self.ai = AIMatch()
        self.app = Application(self.db, self.ai)

    def run(self):
        while True:
            ch = input("1-Register 2-Login 3-Exit:")
            if ch == "1":
                e = input("Email:")
                p = input("Password:")
                n = input("Name:")
                s = input("Skills:")
                ex = int(input("Exp:"))
                r = input("Resume:")
                uid = self.auth.register(e, p, "candidate")
                self.cand.create(uid, n, s, ex, r)
            elif ch == "2":
                e = input("Email:")
                p = input("Password:")
                u = self.auth.login(e, p)
                if u:
                    print("Logged", u["role"])
            else:
                break

if __name__ == "__main__":
    CLI().run()
