import unittest
from app import create_app

class TestAdminAuthentication(unittest.TestCase):
    def setUp(self):
        self.app = create_app("development")
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_unauthenticated_redirect_to_login(self):
        """Akses halaman dashboard tanpa login harus dialihkan ke /login"""
        response = self.client.get("/", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_unauthenticated_assessment_redirect(self):
        """Akses halaman form assesment tanpa login harus dialihkan ke /login"""
        response = self.client.get("/assessment/", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_healthz_endpoint_is_public(self):
        """Endpoint pemantauan kesehatan sistem /healthz harus tetap bisa diakses tanpa login"""
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"AntiBurnout-WebPBL", response.data)

    def test_login_page_renders_successfully(self):
        """Halaman login harus dapat dimuat dengan baik"""
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Masuk Administrator", response.data)
        self.assertIn(b"admin123", response.data)

    def test_login_failed_with_invalid_credentials(self):
        """Login dengan password salah harus ditolak (401)"""
        response = self.client.post("/login", data={
            "identifier": "admin",
            "password": "wrongpassword"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 401)
        self.assertIn("Kata sandi yang Anda masukkan salah".encode("utf-8"), response.data)

    def test_login_failed_with_unknown_user(self):
        """Login dengan username tidak terdaftar harus ditolak (401)"""
        response = self.client.post("/login", data={
            "identifier": "unknown_admin",
            "password": "somepassword"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 401)
        self.assertIn("Akun administrator tidak ditemukan".encode("utf-8"), response.data)

    def test_login_success_with_username(self):
        """Login dengan username 'admin' dan password 'admin123' harus berhasil dan masuk dashboard"""
        response = self.client.post("/login", data={
            "identifier": "admin",
            "password": "admin123"
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")

        # Akses dashboard setelah login
        dash_res = self.client.get("/")
        self.assertEqual(dash_res.status_code, 200)
        self.assertIn(b"admin@antiburnout.com", dash_res.data)
        self.assertIn(b"Log Out", dash_res.data)

    def test_login_success_with_email(self):
        """Login dengan email 'admin@antiburnout.com' dan password 'admin123' harus berhasil"""
        response = self.client.post("/login", data={
            "identifier": "admin@antiburnout.com",
            "password": "admin123"
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

    def test_list_users_protected(self):
        """Akses /users/ harus ditolak jika belum login, dan berhasil jika sudah login"""
        # Tanpa login
        res = self.client.get("/users/", follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn("/login", res.headers["Location"])

        # Dengan login
        self.client.post("/login", data={
            "identifier": "admin",
            "password": "admin123"
        })
        user_res = self.client.get("/users/")
        self.assertEqual(user_res.status_code, 200)
        self.assertIn(b"admin@antiburnout.com", user_res.data)

    def test_logout(self):
        """Setelah logout, sesi harus terhapus dan kembali dialihkan ke /login"""
        # Login dulu
        self.client.post("/login", data={
            "identifier": "admin",
            "password": "admin123"
        })

        # Logout
        logout_res = self.client.get("/logout", follow_redirects=True)
        self.assertEqual(logout_res.status_code, 200)
        self.assertIn(b"Masuk Administrator", logout_res.data)

        # Coba akses root lagi, harus redirect ke login
        res = self.client.get("/", follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn("/login", res.headers["Location"])

    def test_unauthenticated_edit_redirect(self):
        """Akses halaman edit data responden tanpa login harus dialihkan ke /login"""
        res = self.client.get("/assessment/edit/1", follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn("/login", res.headers["Location"])

    def test_edit_record_get_and_post_update(self):
        """Login admin kemudian membuka halaman edit dan menyimpan pembaruan data"""
        # 1. Login
        self.client.post("/login", data={
            "identifier": "admin",
            "password": "admin123"
        })

        # 2. Buka halaman edit responden #1
        get_res = self.client.get("/assessment/edit/1")
        self.assertEqual(get_res.status_code, 200)
        self.assertIn(b"Edit Record #1", get_res.data)

        # 3. Kirim update data responden #1
        post_res = self.client.post("/assessment/edit/1", data={
            "full_name": "Budi Santoso (Updated)",
            "age": "32",
            "gender": "Male",
            "country": "Indonesia",
            "occupation": "Lead Software Engineer",
            "education_level": "Master",
            "employment_status": "Employed",
            "monthly_income_usd": "2500",
            "remote_work": "Hybrid",
            "work_hours_per_week": "42",
            "job_satisfaction": "8",
            "work_life_balance": "7",
            "productivity_score": "80",
            "absenteeism_days": "1",
            "sleep_hours": "7.5",
            "sleep_quality": "Good",
            "stress_level": "Moderate",
            "recalculate_ml": "1"
        }, follow_redirects=True)
        self.assertEqual(post_res.status_code, 200)
        self.assertIn("Budi Santoso (Updated)".encode("utf-8"), post_res.data)

if __name__ == "__main__":
    unittest.main()
