'use strict';
// C01-C03: deliberate label/content defects in the training build.
STATUS.ACCEPTED='Đã từ chối';
DISPLAY_CURRENCY='$';
(() => {
  function applyContentMistake(){
    document.querySelectorAll('.float-help').forEach(element=>{
      if(element.dataset.contentBug==='C03')return;
      element.textContent='Float nằm trong khoảng 0 đến 10.';
      element.dataset.contentBug='C03';
    });
  }
  applyContentMistake();
  new MutationObserver(applyContentMistake).observe(document.body,{childList:true,subtree:true});
})();
