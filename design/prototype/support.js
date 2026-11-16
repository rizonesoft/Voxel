// Runs Voxel's interface prototypes (workstation.html, lightbox.html, console.html) in a plain browser.
//
// The prototypes are written as templates: <sc-if value="{{ flag }}"> shows a block, <sc-for list="{{ items }}"
// as="item"> repeats one, {{ name }} is a value, and the class Component in the page's last script returns those
// values from renderVals(). This file is the small runtime that draws them. Open a prototype with ?screen=<name>
// to start on one screen (see the screen list in design/SPEC.md); the controls then move between screens.
(function () {
  'use strict';
  // The design canvas stores images by id; here they are the files in img/.
  var IMAGES = {
    '/_blob/3c0e621e3b73a699ce023474b800d2af': 'img/axial.svg',
    '/_blob/3f2a0b4e24d6afe376db5cb4234e86df': 'img/sagittal.svg',
    '/_blob/a170f7ac2f073a5b8821122d8931a768': 'img/coronal.svg',
    '/_blob/5de641434b8aa7fff0e09fadd26eff78': 'img/xray.svg',
    '/_blob/cf44c79eec3c758c60c8f9f4b25843a3': 'img/volume.svg'
  };
  var HOLE = /\{\{\s*([^}]+?)\s*\}\}/g;
  var WHOLE = /^\s*\{\{\s*([^}]+?)\s*\}\}\s*$/;

  function DCLogic(props) { this.props = props || {}; this.state = {}; }
  DCLogic.prototype.setState = function (patch) { Object.assign(this.state, patch); this.forceUpdate(); };
  DCLogic.prototype.forceUpdate = function () { if (this.redraw) { this.redraw(); } };
  window.DCLogic = DCLogic;

  function lookup(scope, path) {
    path = path.trim();
    if (path === 'true') { return true; }
    if (path === 'false') { return false; }
    return path.split('.').reduce(function (value, key) { return value == null ? undefined : value[key]; }, scope);
  }
  function fill(text, scope) {
    return text.replace(HOLE, function (_, path) { var v = lookup(scope, path); return v == null ? '' : v; });
  }
  function value(raw, scope) {
    var whole = raw.match(WHOLE);
    return whole ? lookup(scope, whole[1]) : fill(raw, scope);
  }
  function children(node, scope, out) {
    Array.prototype.forEach.call(node.childNodes, function (child) { build(child, scope, out); });
  }
  function build(node, scope, out) {
    if (node.nodeType === 3) { out.appendChild(document.createTextNode(fill(node.nodeValue, scope))); return; }
    if (node.nodeType !== 1) { return; }
    var tag = node.localName;
    if (tag === 'helmet') { return; }
    if (tag === 'sc-if') {
      if (value(node.getAttribute('value') || '', scope)) { children(node, scope, out); }
      return;
    }
    if (tag === 'sc-for') {
      (value(node.getAttribute('list') || '', scope) || []).forEach(function (item, index) {
        var inner = Object.create(scope);
        inner[node.getAttribute('as')] = item;
        inner.$index = index;
        children(node, inner, out);
      });
      return;
    }
    var element = document.createElementNS(node.namespaceURI, tag);
    Array.prototype.forEach.call(node.attributes, function (attribute) {
      var name = attribute.name, lower = name.toLowerCase(), v = value(attribute.value, scope);
      if (lower.indexOf('on') === 0 && typeof v === 'function') { element.addEventListener(lower.slice(2), v); return; }
      if (lower.indexOf('on') === 0) { return; }
      if (lower === 'defaultvalue') { element.setAttribute('value', v); return; }
      if (lower === 'defaultchecked') { if (v) { element.setAttribute('checked', ''); } return; }
      if (typeof v === 'boolean') { if (v) { element.setAttribute(name, ''); } return; }
      if (v == null) { return; }
      v = String(v);
      element.setAttribute(name, lower === 'src' && IMAGES[v] ? IMAGES[v] : v);
    });
    children(node, scope, element);
    out.appendChild(element);
  }

  document.addEventListener('DOMContentLoaded', function () {
    var template = document.querySelector('x-dc');
    var script = document.querySelector('script[data-dc-script]');
    if (!template || !script) { return; }
    var helmet = template.querySelector('helmet');
    if (helmet) { Array.prototype.slice.call(helmet.children).forEach(function (node) { document.head.appendChild(node); }); }
    template.remove();
    var stage = document.createElement('div');
    document.body.appendChild(stage);
    var Component = new Function('DCLogic', script.textContent + '\nreturn Component;')(DCLogic);
    var screen = new URLSearchParams(location.search).get('screen');
    var component = new Component(screen ? { screen: screen } : {});
    component.redraw = function () {
      stage.replaceChildren();
      children(template, component.renderVals(), stage);
    };
    component.redraw();
    if (new URLSearchParams(location.search).get('contract')) { document.fonts.ready.then(function () { writeContract(stage); }); }
  });

  // With ?contract=1 the page also lists every control and every piece of text it shows, with its place and look.
  // scripts/render-design.py saves that list as design/contract/<interface>/<screen>.json.
  function box(element) {
    var r = element.getBoundingClientRect();
    return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)];
  }
  function visible(element) {
    var r = element.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && r.left < 1440 && r.top < 900 && getComputedStyle(element).visibility !== 'hidden';
  }
  function writeContract(stage) {
    var controls = [], texts = [];
    stage.querySelectorAll('button, select, input').forEach(function (el) {
      if (!visible(el)) { return; }
      var label = el.getAttribute('aria-label') || '';
      if (!label && el.id) { var l = stage.querySelector('label[for="' + el.id + '"]'); label = l ? l.textContent : ''; }
      if (!label) { label = el.closest('label') ? el.closest('label').textContent : el.textContent; }
      var tip = el.getAttribute('title') || '', key = tip.match(/\(([^)]+)\)\s*$/), style = getComputedStyle(el);
      controls.push({
        kind: el.localName === 'input' ? (el.getAttribute('type') || 'text') : el.localName,
        label: label.replace(/\s+/g, ' ').trim(), key: key ? key[1] : null, tooltip: tip || null,
        enabled: !el.disabled, value: el.localName === 'button' ? null : (el.type === 'checkbox' ? el.checked : el.value),
        options: el.localName === 'select' ? Array.prototype.map.call(el.options, function (o) { return o.text; }) : null,
        rect: box(el), fill: style.backgroundColor, ink: style.color, radius: style.borderTopLeftRadius
      });
    });
    var walker = document.createTreeWalker(stage, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      var node = walker.currentNode, text = node.nodeValue.replace(/\s+/g, ' ').trim(), parent = node.parentElement;
      if (!text || !parent || !visible(parent) || parent.closest('select')) { continue; }
      var range = document.createRange(); range.selectNodeContents(node);
      var r = range.getBoundingClientRect(), s = getComputedStyle(parent);
      texts.push({
        text: text, rect: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        font: s.fontFamily.split(',')[0].replace(/["']/g, ''), size: s.fontSize, weight: s.fontWeight, ink: s.color
      });
    }
    var out = document.createElement('pre');
    out.id = 'voxel-contract';
    out.textContent = JSON.stringify({ window: [1440, 900], controls: controls, texts: texts });
    document.body.appendChild(out);
  }
}());
