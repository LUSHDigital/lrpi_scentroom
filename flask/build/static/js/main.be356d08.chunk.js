(this["webpackJsonplush-file-uploader"]=this["webpackJsonplush-file-uploader"]||[]).push([[0],{10:function(e,t,n){e.exports=n(15)},15:function(e,t,n){"use strict";n.r(t);var a=n(2),l=n(3),o=n(5),r=n(4),c=n(6),i=n(0),u=n.n(i),d=n(9),s=n.n(d);n(8),Boolean("localhost"===window.location.hostname||"[::1]"===window.location.hostname||window.location.hostname.match(/^127(?:\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}$/));var h=n(1),m=function(e){function t(e){var n;return Object(a.a)(this,t),(n=Object(o.a)(this,Object(r.a)(t).call(this,e))).fileChangeHandler=function(e){var t=e.target.files[0];n.setState({selectedFile:t})},n.colorChangeHandler=function(e){var t=e.target.value;n.setState({selectedCol:t})},n.handleSubmit=function(e){e.preventDefault();var t=new FormData;t.append("file",n.state.selectedFile),t.append("colour",n.state.selectedCol),n.uploadFile(t),n.uploadCol(t)},n.state={selectedFile:null,selectedCol:"#011993"},n.fileChangeHandler=n.fileChangeHandler.bind(Object(h.a)(n)),n.handleSubmit=n.handleSubmit.bind(Object(h.a)(n)),n.colorChangeHandler=n.colorChangeHandler.bind(Object(h.a)(n)),n}return Object(c.a)(t,e),Object(l.a)(t,[{key:"render",value:function(){return u.a.createElement("div",{className:"form_body"},u.a.createElement("form",{onSubmit:this.handleSubmit},u.a.createElement("label",null,"Select Music File"),u.a.createElement("br",null),u.a.createElement("input",{type:"file",id:"fileinput",name:"file",accept:".mp3,.mp4;",onChange:this.fileChangeHandler}),u.a.createElement("br",null),u.a.createElement("label",null,"Select Colour"),u.a.createElement("br",null),u.a.createElement("br",null),u.a.createElement("input",{type:"color",name:"colour",onChange:this.colorChangeHandler,value:this.state.selectedCol})," ",u.a.createElement("br",null),u.a.createElement("input",{type:"submit",value:"Upload",id:"inputbtn"})))}},{key:"uploadFile",value:function(e){var t=window.location.origin+"/uploadfile";fetch(t,{method:"POST",body:e}).catch((function(e){return console.log(e)}))}},{key:"uploadCol",value:function(e){var t=window.location.origin+"/uploadcol";fetch(t,{method:"POST",body:e}).catch((function(e){return console.log(e)}))}}]),t}(u.a.Component),p=function(e){function t(){return Object(a.a)(this,t),Object(o.a)(this,Object(r.a)(t).apply(this,arguments))}return Object(c.a)(t,e),Object(l.a)(t,[{key:"render",value:function(){return u.a.createElement("div",null,u.a.createElement("div",{className:"layout_header"},u.a.createElement("h1",null,"File uploader")),u.a.createElement(m,null))}}]),t}(u.a.Component);s.a.render(u.a.createElement(p,null),document.getElementById("root")),"serviceWorker"in navigator&&navigator.serviceWorker.ready.then((function(e){e.unregister()}))},8:function(e,t,n){}},[[10,1,2]]]);
//# sourceMappingURL=main.be356d08.chunk.js.map