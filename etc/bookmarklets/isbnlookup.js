var isbn13_label = $('table#productDetailsTable').find("b:contains('ISBN-13')");
if (isbn13_label.length){
    var isbn13 = isbn13_label[0].nextSibling.nodeValue.trim().replace('-', '');
    var bnmhead = 'https://labs.library.link/example/nearbyisbn.html?isbn=';
    var bnmtail = '&radius=100';
    window.location = bnmhead+isbn13+bnmtail;
} else {
    alert('ISBN-13 not found on page.');
}
