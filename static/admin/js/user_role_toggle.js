(function ($) {
    $(function () {
        var roleInput = $("#id_role");
        var encadrantsRow = $(".form-row.field-encadrants, .field-encadrants");
        if (!encadrantsRow.length) encadrantsRow = $("#id_encadrants").closest("div");
        var groupesRow = $(".form-row.field-groupes_etudiant, .field-groupes_etudiant");
        if (!groupesRow.length) groupesRow = $("#id_groupes_etudiant").closest("div");

        function toggleEtudiantFields() {
            var isEtudiant = roleInput.val() === "ETUDIANT";
            if (isEtudiant) {
                encadrantsRow.show();
                groupesRow.show();
            } else {
                encadrantsRow.hide();
                groupesRow.hide();
            }
        }

        roleInput.on("change", toggleEtudiantFields);
        toggleEtudiantFields();
    });
})(django.jQuery);
