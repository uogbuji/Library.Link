
# Install

[Can't easily host the bookmarklets](https://github.com/github/markup/issues/79) on GitHub, so coming soon…

## isbnlookup.js

Code:

    javascript:(function()%7Bfunction callback()%7B(function(%24)%7Bvar jQuery%3D%24%3Bvar isbn13 %3D null%3Bvar am_isbn13_label %3D %24('table%23productDetailsTable').find("b%3Acontains('ISBN-13')")%3Bvar bn_isbn13_label %3D %24('div%23ProductDetailsTab').find("th%3Acontains('ISBN-13')")%3Bif (am_isbn13_label.length)%7Bvar isbn13 %3D am_isbn13_label%5B0%5D.nextSibling.nodeValue.trim().replace('-'%2C '')%3B%7D else if (bn_isbn13_label.length) %7Bvar isbn13 %3D bn_isbn13_label.next('td').text().trim().replace('-'%2C '')%3B%7Dif (isbn13 !%3D null) %7Bvar bnmhead %3D 'https%3A%2F%2Flabs.library.link%2Fexample%2Fnearbyisbn.html%3Fisbn%3D'%3Bvar bnmtail %3D '%26radius%3D100'%3Bwindow.location %3D bnmhead%2Bisbn13%2Bbnmtail%3B%7D else %7Balert('ISBN-13 not found on page.')%3B%7D%7D)(jQuery.noConflict(true))%7Dvar s%3Ddocument.createElement("script")%3Bs.src%3D"https%3A%2F%2Fajax.googleapis.com%2Fajax%2Flibs%2Fjquery%2F1.11.1%2Fjquery.min.js"%3Bif(s.addEventListener)%7Bs.addEventListener("load"%2Ccallback%2Cfalse)%7Delse if(s.readyState)%7Bs.onreadystatechange%3Dcallback%7Ddocument.body.appendChild(s)%3B%7D)()

# For developers

Can use [the MrColes bookmarklet creator](https://mrcoles.com/bookmarklet/) on the source .js files in this directory.

# Notes on isbnlookup.js

Use the jQuery option with the bookmarklet creator.

[JS Fiddle for extracting ISBN-13 from page content](https://jsfiddle.net/uogbuji/xpvt214o/662826/)

If we could trust there to be an ISBN in the URL we could use:

    setTimeout('llpop.focus()',300);
    var re=/([\/-]|is[bs]n=)(\d{7,9}[\dX])/i;
    if(re.test(location.href)==true)
    {
        var isbn10=RegExp.$2;
        var chars = isbn10.split("");
        chars.unshift("9", "7", "8");
        chars.pop();

        var i = 0;
        var sum = 0;
        for (i = 0; i < 12; i += 1) {
              sum += chars[i] * ((i % 2) ? 3 : 1);
        }
        var check_digit = (10 - (sum % 10)) % 10;
        chars.push(check_digit);

        var isbn13 = chars.join("");
        var bnmhead = 'https://labs.library.link/example/nearbyisbn.html?isbn='
        var bnmtail = '&radius=100'
        var llpop= window.open(bnmhead+isbn13+bnmtail,'ISBN near me','scrollbars=1,resizable=1,top=0,left=0,location=1,width=800,height=600');
        llpop.focus();
    }

(uses a variation of the function defined in ["Converting ISBN-10 to ISBN-13"](http://www.dispersiondesign.com/articles/isbn/converting_isbn10_to_isbn13))

If not for popup blocker problems we could do:

    var isbn13_label = $('table#productDetailsTable').find("b:contains('ISBN-13')");
    if (isbn13_label.length){
        var isbn13 = isbn13_label[0].nextSibling.nodeValue.trim().replace('-', '');
        var bnmhead = 'https://labs.library.link/example/nearbyisbn.html?isbn=';
        var bnmtail = '&radius=100';
        window.open(bnmhead+isbn13+bnmtail,'ISBN near me','scrollbars=1,resizable=1,top=0,left=0,location=1,width=800,height=600');
    } else {
        alert('ISBN-13 not found on page.');
    }


# Favicon

I [created a Favico](https://www.favicon-generator.org/) from [this CC0 image](https://pixabay.com/en/icon-position-map-location-icon-2070751/).

    <link rel="apple-touch-icon" sizes="57x57" href="/apple-icon-57x57.png">
    <link rel="apple-touch-icon" sizes="60x60" href="/apple-icon-60x60.png">
    <link rel="apple-touch-icon" sizes="72x72" href="/apple-icon-72x72.png">
    <link rel="apple-touch-icon" sizes="76x76" href="/apple-icon-76x76.png">
    <link rel="apple-touch-icon" sizes="114x114" href="/apple-icon-114x114.png">
    <link rel="apple-touch-icon" sizes="120x120" href="/apple-icon-120x120.png">
    <link rel="apple-touch-icon" sizes="144x144" href="/apple-icon-144x144.png">
    <link rel="apple-touch-icon" sizes="152x152" href="/apple-icon-152x152.png">
    <link rel="apple-touch-icon" sizes="180x180" href="/apple-icon-180x180.png">
    <link rel="icon" type="image/png" sizes="192x192"  href="/android-icon-192x192.png">
    <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="96x96" href="/favicon-96x96.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
    <link rel="manifest" href="/manifest.json">
    <meta name="msapplication-TileColor" content="#ffffff">
    <meta name="msapplication-TileImage" content="/ms-icon-144x144.png">
    <meta name="theme-color" content="#ffffff">

# Resources

* [JS based bookmarklet builder](https://github.com/kostasx/make_bookmarklet), could easily be ported to Python
