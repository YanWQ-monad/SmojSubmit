from unittest import TestCase

from SmojSubmit.libs.middleware import freopen_filter


class TestMiddleware(TestCase):
    def test_freopen(self):
        self.assertEqual(freopen_filter('freopen("Temp.in", "r", stdin);'), '')
        self.assertEqual(freopen_filter('freopen ( "Temp.in" ,"r" ,stdin ) ;'), '')
        self.assertEqual(freopen_filter('freopen    (   "Temp.in" , "r" ,stdin ) ;'), '')
        self.assertEqual(freopen_filter('freopen ("Temp.in" , "r", stdin );', '1234'),
                         'freopen ("1234.in" , "r", stdin );')
        self.assertEqual(freopen_filter('freopen ("Temp.ans" , "w", stderr);', '1234'),
                         'freopen ("1234.ans" , "w", stderr);')
        self.assertEqual(freopen_filter('// freopen("Temp.out" , "w", stdout);', '1234'),
                         'freopen("1234.out" , "w", stdout);')
        self.assertEqual(freopen_filter('    // freopen("Temp.out" , "w", stdout);', '1234'),
                         '    freopen("1234.out" , "w", stdout);')
