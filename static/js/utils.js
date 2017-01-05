$( function() {

    $(".datepicker").datepicker({ dateFormat: 'yy-mm-dd HH:MM:SS' });

    $(".search")
        .keyup(function () {
            var url = "/search_airport/" + $(this).find('input').val();
            $(this).children('.search-results').load(url);
        })
        .on('click', '.search-item', function () {
            var $this = $(this);
            $this.closest('.search').find('input').val( $this.text());
            $this.parent('ul').html(null);
        });
} );
