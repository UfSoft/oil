/*
 * $Id$
 * vim: sw=2 ts=2 fenc=utf-8
 *
 * PNG Fix - Simple plugin to fix IE png transparency
 *
 * Copyright (c) Pedro Algarvio (http://ufsoft.org)
 * Licensed under the BSD license.
 *
 * Version: 0.1
 */

jQuery.fn.pngFix = function(o) {
  console.log(this);
  return this.each( function() {
    var isIE = navigator.appVersion.split("MSIE");
    var version = parseFloat(isIE[1]);
    /*
    // Browser Check
    if ( jQuery.browser.version.number() ) {
      // we heve jQBrowser Plugin
      var isIE = jQuery.browser.msie();
      var version = jQuery.browser.version.number();
    } else {
      var isIE = navigator.appVersion.split("MSIE");
      var version = parseFloat(isIE[1]);
    };*/

    var img = this;
    var imgName = img.src.toUpperCase();
    if (imgName.substring(imgName.length-3, imgName.length) == "PNG") {
      id = jQuery(img).attr('id');
      class = jQuery(img).attr('class');
      title = jQuery(img).attr('title'); /*
      if ( jQuery(img).css() ) {
        style = jQuery(img).css().css('display', 'inline-block');
      } else {
        style = {display: 'inline-block'};
      }; */
      if ( jQuery(img).attr('align') ) jQuery(img).css('float', jQuery(img).attr('align'));
      if (jQuery(img).parent().attr('href')) jQuery(img).css('cursor', 'hand');
      span = jQuery('<span></span>').get(0);
      if ( id ) jQuery(span).attr('id', id);
      if ( class ) jQuery(span).attr('class', class);
      if ( title ) jQuery(span).attr('title', title);
      style = {display: 'inline-block'};
      msDX = 'progid:DXImageTransform.Microsoft.AlphaImageLoader(src="' + jQuery(img).attr('src') + '", sizingMethod="scale")';
      console.log(msDX);
      jQuery(span).css(style).css( 'filter', msDX );
      /*
        'filter', 'progid:DXImageTransform.Microsoft.AlphaImageLoader(src="' + 
        jQuery(img).attr('src') + '", sizingMethod="scale")';
      );*/
      console.log(span);
      jQuery(img).wrap(span);
    };
  });
};

/*
    ddd//browser = jQuery.browser.msie();
    version = parseInt(navigator.appVersion.split("MSIE")[1]);
    //console.log(browser);
    //console.log(jQuery.browser.version.number());
    a = true;
    console.log(img.src);
    

      //console.log(img)
      var imgName = img.src.toUpperCase()
      //console.log(imgName)
      //console.log(img.src)
      if (imgName.substring(imgName.length-3, imgName.length) == "PNG")
      {
         var imgID = (img.id) ? "id='" + img.id + "' " : ""
         var imgClass = (img.className) ? "class='" + img.className + "' " : ""
         var imgTitle = (img.title) ? "title='" + img.title + "' " : "title='" + img.alt + "' "
         var imgStyle = "display:inline-block;" + img.style.cssText
         if (img.align == "left") imgStyle = "float:left;" + imgStyle
         if (img.align == "right") imgStyle = "float:right;" + imgStyle
         //if (img.parentElement.href) imgStyle = "cursor:hand;" + imgStyle
         var strNewHTML = "<span " + imgID + imgClass + imgTitle
         + " style=\"" + "width:" + img.width + "px; height:" + img.height + "px;" + imgStyle + ""
         + "filter:progid:DXImageTransform.Microsoft.AlphaImageLoader"
         + "(src=\'" + img.src + "\', sizingMethod='scale');\"></span>"
         img.outerHTML = strNewHTML
        console.log(strNewHTML)
/*      }

/*    //if ( jQuery.browser.msie && version < 7 ) {
    if ( a ) {
      id = (this.id) ? "id='" + this.id + "' " : "";
      class = (this.class) ? "class='" + this.class + "' " : "";
      title = (this.title) ? "title='" + this.title + "' " : "";
      style = "display:inline-block;" + this.style.cssText;
      if ( this.align == 'left' ) style = "float:left;" + style;
      if ( this.align == 'right' ) style = "float:right;" + style;
      //if ( this.parentElement.href ) style = "cursor:hand;" + style;
      var strNewHTML = "<span " + imgID + imgClass + imgTitle
      + " style=\"" + "width:" + img.width + "px; height:" + img.height + "px;" + imgStyle + ";"
      + "filter:progid:DXImageTransform.Microsoft.AlphaImageLoader"
      + "(src=\'" + img.src + "\', sizingMethod='scale');\"></span>"
      img.outerHTML = strNewHTML
/*      jQuery(this).wrap(
        '<span ' + id + class + title + 'style="width:' + this.width +
        'px; height: ' + this.height + 'px; ' + style +
        '; filter:progid:DXImageTransform.Microsoft.AlphaImageLoader' +
        "src='" + this.src + "', sizingMethod='scale');\"></span>"
      );*/
      //jQuery(this).wrap(newelem);
      //jQuery(this).remove();
      //this.outerHTML = newelem;
      //console.log(this.src);
      /*jQuery(this).css(
        {
          height: this.height + 'px',
          width: this.width + 'px',
          behaviour: 'url(./iepngfix.htc)'
        }
      );*/ /*
    };
  });
};
*/

