// Add <option> to <select>
function new_option(select_id, question) {
  var name = prompt(question);
  if ( name ) {
    if ( name.charAt(0) == '#' ) {
        name = name.substring(1, name.length);
    };
    $(select_id).addOption(name, name, false);
    $(select_id).sortOptions();
  };
};

// Remove <option> from <select>
function remove_option(select_id) {
  $(select_id+'/option:selected').each(function() {
    $(select_id).removeOption(this.value);
  });
};

// Select all <option>'s from <select>
function select_all_options(select_id) {
  $(select_id+'/option').each(function() {
    $(this).attr('selected', true);
  });
};