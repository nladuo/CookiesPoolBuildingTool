<template>
  <div class="wrapper">
    <h1>Cookie Pool Building Tool</h1><br><br>

    <Row>
      <i-col span="5">
        <label>cookie服务器地址：</label>
      </i-col>
      <i-col span="18">
        <Input v-model="server_url" placeholder="输入cookie服务器地址" style="width: 300px" />
      </i-col>
    </Row>
    <br>

    <Row>
      <i-col span="5">
        <label>cookie服务器密码：</label>
      </i-col>
      <i-col span="18">
        <Input v-model="server_passwd" type="password" placeholder="输入cookie服务器的密码" style="width: 300px" />
      </i-col>
    </Row>
    <br>

    <Row>
      <i-col span="5">
        <label>默认打开网页：</label>
      </i-col>
      <i-col span="18">
        <Input v-model="base_url" placeholder="输入默认打开的网址" style="width: 300px" />
      </i-col>
    </Row>
    <br>

    <Button @click="saveConfig">保存配置</Button>&nbsp;&nbsp;
    <Button type="success" @click="checkServerValid">测试服务器连通</Button>
    <br><br>

    <div v-if="server_valid">
      <h2>人工操作：</h2>
      <Button type="primary" @click="openChrome" :disabled="open_disabled" >打开chrome</Button>&nbsp;&nbsp;
      <Button type="info" @click="sendCookie" :disabled="cookie_disabled" >提交cookie</Button>&nbsp;&nbsp;
      <Button type="error" @click="exitChrome" >退出浏览器</Button>&nbsp;&nbsp;

      <br><br>
      <h2>已有cookie：</h2>
      <Table border :columns="columns" :data="cookies"></Table>

    </div>

  </div>
</template>

<script>
  import ICol from "../../../node_modules/iview/src/components/grid/col.vue";

  export default {
      components: {ICol},
      name: 'main-page',
      data() {
          return {
              server_url: "",
              server_passwd: "",
              base_url: "",
              driver: null,
              open_disabled: false,
              cookie_disabled: true,
              cookies: [],
              columns: [
                  {
                      title: 'CookieId',
                      key: 'id',
                  },
                  {
                      title: 'MD5',
                      key: 'md5',
                  },
                  {
                      title: '创建时间',
                      key: 'update_time',
                  },
              ],
              cookieCount: 0,
              mydb: "",
              server_valid: false
          }
      },
      created() {
          let Datastore = require('nedb');
          this.mydb = new Datastore({ filename: 'cookies-pool-tool.db', autoload: true });
          this.loadConfig();
      },
      methods: {
          /**
           * 校验服务器配置是否正确
           */
          checkServerValid() {
              this.$Spin.show();
              this.$http.get(this.server_url + "/",
                  {
                    params:{
                      passwd: this.server_passwd
                    }
                  }).then((response) => {
                      this.$Spin.hide();
                      if (response.data.code === 200 && response.data.msg === 'pong') {
                          this.$Notice.success({
                              title: '成功',
                              desc: 'Cookie服务器校验成功',
                              duration: 3
                          });
                          this.server_valid = true;
                      } else {
                          this.$Notice.error({
                              title: '失败',
                              desc: '服务器密码错误',
                              duration: 0
                          });
                      }
                      console.log(response.data);
                  }).catch((error) => {
                      this.$Spin.hide();
                      console.log(error);
                      this.$Notice.error({
                          title: '失败',
                          desc: '网络异常',
                          duration: 0
                      });
                  });
          },
          openChrome () {
              let webdriver = require('selenium-webdriver');

              this.driver = new webdriver.Builder()
                  .forBrowser('chrome')
                  .build();

              this.driver.get(this.base_url);
              this.open_disabled = true;
              this.cookie_disabled = false;
          },
          sendCookie() {
              this.$Spin.show();
              this.driver.manage()
                  .getCookies()
                  .then((cookies)=> {
                      let cookies_str = JSON.stringify(cookies);
                      console.log(cookies_str);
                      this.addCookieHttp(cookies_str, ()=> {
                          this.$Spin.hide();
                          // 成功则关闭chrome
                          this.driver.quit();
                          this.open_disabled = false;
                          this.cookie_disabled = true;
                      })
                  });
          },
          exitChrome() {
              this.driver.quit();
              this.open_disabled = false;
              this.cookie_disabled = true;
          },
          saveConfig() {
              this.mydb.find({id: 1}, (err, docs) => {
                  if (docs.length === 0) {
                      // insert config
                      this.mydb.insert({
                          id: 1,
                          server_url: this.server_url,
                          server_passwd: this.server_passwd,
                          base_url: this.base_url
                      })

                  } else {
                      // update config
                      this.mydb.update({id: 1},
                          {
                              $set: {
                                  server_url: this.server_url,
                                  server_passwd: this.server_passwd,
                                  base_url: this.base_url
                              }
                          },
                          {});
                  }
                  if (err === null) {
                      this.$Notice.success({
                          title: '成功',
                          desc: '保存设置成功',
                          duration: 5
                      });
                  } else {
                      this.$Notice.error({
                          title: '失败',
                          desc: '保存设置失败',
                          duration: 5
                      });
                  }
              });

          },
          loadConfig() {
              this.mydb.find({id: 1}, (err, docs) => {
                  if (docs.length === 1) {
                      this.server_url = docs[0].server_url;
                      this.base_url = docs[0].base_url;
                      this.server_passwd = docs[0].server_passwd;
                  }
              });
          },
          /**
           * 添加cookie的Http请求
           * @param cookies_str
           * @param success_callback
           */
          addCookieHttp(cookies_str, success_callback) {

              this.$http.get(this.server_url + "/add_cookie",
                  {
                      params:{
                          passwd: this.server_passwd,
                          cookies: cookies_str
                      }
                  }).then((response) => {
                  if (response.data.code === 200) {
                      this.$Notice.success({
                          title: '成功',
                          desc: '添加cookie成功',
                          duration: 3
                      });
                      success_callback()
                  } else if (response.data.code === 502) {
                      this.$Notice.error({
                          title: '失败',
                          desc: '此cookie未能通过服务器校验',
                          duration: 0
                      });
                  } else if (response.data.code === 503) {
                      this.$Notice.error({
                          title: '失败',
                          desc: '请勿添加重复的cookie',
                          duration: 0
                      });
                  }
                  console.log(response.data);
              }).catch((error) => {

                  console.log(error);
                  this.$Notice.error({
                      title: '失败',
                      desc: '网络异常',
                      duration: 0
                  });
              });
          },
          getCookiesHttp() {
              this.$http.get(this.server_url + "/add_cookie",
                  {
                      params:{
                          passwd: this.server_passwd,
                          cookies: cookies_str
                      }
                  }).then((response) => {
                  if (response.data.code === 200) {
                      this.$Notice.success({
                          title: '成功',
                          desc: '添加cookie成功',
                          duration: 3
                      });
                  } else if (response.data.code === 502) {
                      this.$Notice.error({
                          title: '失败',
                          desc: '此cookie未能通过服务器校验',
                          duration: 0
                      });
                  }
                  console.log(response.data);
              }).catch((error) => {

                  console.log(error);
                  this.$Notice.error({
                      title: '失败',
                      desc: '网络异常',
                      duration: 0
                  });
              });

          }
      }
  }
</script>

<style scoped>
  .wrapper{
    margin: 20px;
  }

  label{
    line-height: 32px;
  }
</style>

