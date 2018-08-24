var isbn13 = null;
var gr_isbn13 = $('meta[property="books:isbn"]').attr("content");
var am_isbn13_label = $('table#productDetailsTable').find("b:contains('ISBN-13')");
var bn_isbn13_label = $('div#ProductDetailsTab').find("th:contains('ISBN-13')");
if (typeof gr_isbn13 != 'undefined'){
    var isbn13 = gr_isbn13;
} else if (am_isbn13_label.length){
    var isbn13 = am_isbn13_label[0].nextSibling.nodeValue.trim().replace('-', '');
} else if (bn_isbn13_label.length) {
    var isbn13 = bn_isbn13_label.next('td').text().trim().replace('-', '');
}
if (isbn13 != null) {
    var bnmhead = 'https://labs.library.link/example/nearbyisbn.html?isbn=';
    var bnmtail = '&radius=100&embed=true&referrer='+encodeURI(window.location);
    window.location = bnmhead+isbn13+bnmtail;
} else {
    alert('ISBN-13 not found on page.');
}
