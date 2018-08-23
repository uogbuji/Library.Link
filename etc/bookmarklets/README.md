
Use [the MrColes bookmarklet creator](https://mrcoles.com/bookmarklet/)

## Notes on isbnlookup.js

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


# Resources

* [JS based bookmarklet builder](https://github.com/kostasx/make_bookmarklet), could easily be ported to Python
