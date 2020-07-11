$(document).ready(function(){
    $('.dropdown-nevbar').on('show.bs.dropdown', function() {
        $(this).find('.dropdown-menu-nevbar').first().stop(true, true).slideDown();
    });

    // Add slideUp animation to Bootstrap dropdown when collapsing.
    $('.dropdown-nevbar').on('hide.bs.dropdown', function() {
        $(this).find('.dropdown-menu-nevbar').first().stop(true, true).slideUp();
    });
});