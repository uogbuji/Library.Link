var isbn13 = null;
var am_isbn13_label = $('table#productDetailsTable').find("b:contains('ISBN-13')");
var bn_isbn13_label = $('div#ProductDetailsTab').find("th:contains('ISBN-13')");
if (am_isbn13_label.length){
    var isbn13 = am_isbn13_label[0].nextSibling.nodeValue.trim().replace('-', '');
} else if (bn_isbn13_label.length) {
    var isbn13 = bn_isbn13_label.next('td').text().trim().replace('-', '');
}
if (isbn13 != null) {
    var bnmhead = 'https://labs.library.link/example/nearbyisbn.html?isbn=';
    var bnmtail = '&radius=100';
    window.location = bnmhead+isbn13+bnmtail;
} else {
    alert('ISBN-13 not found on page.');
}
