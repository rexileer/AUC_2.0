(function ($) {
  $.extend($.fn.select2.amd, {
    default: function () {
      return {
        translations: {
          pl: {
            errorLoading: function () {
              return "Nie można załadować wyników.";
            },
            inputTooLong: function (args) {
              var overChars = args.input.length - args.maximum;
              return (
                "Proszę usunąć " +
                overChars +
                " znak" +
                (overChars === 1 ? "" : "i") +
                "."
              );
            },
            inputTooShort: function (args) {
              var remainingChars = args.minimum - args.input.length;
              return (
                "Proszę wpisać jeszcze " +
                remainingChars +
                " znak" +
                (remainingChars === 1 ? "" : "i") +
                "."
              );
            },
            loadingMore: function () {
              return "Ładowanie więcej wyników...";
            },
            maximumSelected: function (args) {
              return (
                "Możesz wybrać tylko " +
                args.maximum +
                " element" +
                (args.maximum === 1 ? "" : "y") +
                "."
              );
            },
            noResults: function () {
              return "Brak wyników.";
            },
            searching: function () {
              return "Wyszukiwanie...";
            },
          },
        },
      };
    },
  });
})(jQuery);
