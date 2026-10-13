import unittest

from app import app, find_books, shortest_path

class LibARTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_health(self):
        r=self.client.get('/health')
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json['status'],'ok')

    def test_stats(self):
        r=self.client.get('/api/stats')
        self.assertEqual(r.status_code,200)
        self.assertGreaterEqual(r.json['titles'],20)
        self.assertGreaterEqual(r.json['shelves'],6)

    def test_search(self):
        r=self.client.get('/api/books?q=machine%20learning')
        self.assertEqual(r.status_code,200)
        self.assertGreater(len(r.json),0)
        self.assertEqual(r.json[0]['title'],'Hands-On Machine Learning')

    def test_abbreviation_search(self):
        r=self.client.get('/api/books?q=DBMS')
        self.assertEqual(r.status_code,200)
        self.assertGreater(len(r.json),0)

    def test_recommendations(self):
        r=self.client.get('/api/recommendations?q=machine%20learning')
        self.assertEqual(r.status_code,200)
        self.assertGreater(len(r.json),0)

    def test_routes(self):
        for shelf in ['CS_SHELF','AI_SHELF','DB_SHELF','NETWORK_SHELF']:
            r=self.client.get('/api/route?target='+shelf)
            self.assertEqual(r.status_code,200)
            self.assertEqual(r.json['path'][0],'ENTRANCE')
            self.assertEqual(r.json['path'][-1],shelf)

    def test_invalid_shelf(self):
        r=self.client.get('/api/route?target=UNKNOWN')
        self.assertEqual(r.status_code,400)

    def test_direct_algorithm(self):
        path,distance=shortest_path('ENTRANCE','AI_SHELF')
        self.assertEqual(path[-1],'AI_SHELF')
        self.assertGreater(distance,0)

    def test_suggestions(self):
        r = self.client.get('/api/suggest?q=learn')
        self.assertEqual(r.status_code, 200)
        self.assertIsInstance(r.json, list)
        self.assertGreater(len(r.json), 0)

    def test_markers(self):
        r = self.client.get('/api/markers')
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(len(r.json), 1)

    def test_route_maneuvers(self):
        r = self.client.get('/api/route?target=AI_SHELF&start=ENTRANCE')
        self.assertEqual(r.status_code, 200)
        self.assertIn('maneuvers', r.json)
        self.assertIn('distance_meters', r.json)
        self.assertGreater(len(r.json['maneuvers']), 0)
        self.assertEqual(r.json['maneuvers'][-1]['to_node'], 'AI_SHELF')

    def test_book_category_filter(self):
        r = self.client.get('/api/books?category=Database')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(all(b['category'] == 'Database' or b['subject'] == 'Database' for b in r.json))

    def test_pwa_manifest(self):
        r = self.client.get('/manifest.json')
        self.assertEqual(r.status_code, 200)
        self.assertIn('name', r.json)
        r.close()

if __name__=='__main__':
    unittest.main()
