// Set refresh time in milliseconds.
var timeout = '3000'

// Animates string replacement only when there are changes.
function replace(element, string) {
    if (element.text() != string) {
        element.fadeOut('slow', function() { element.text(string)});
        element.fadeIn('slow');
    }
};

// Reload loop to get new post information and update page.
var reload = setInterval(
    function() {
        $.ajax({
            dataType: "json",
            url: 'post.json',
            cache: false,
            success: function(data){
                replace($('span#message'),   data.message);
                replace($('span#author'),    data.author);
                replace($('span#timestamp'), data.timestamp);
            }
        });
    }, timeout
);
