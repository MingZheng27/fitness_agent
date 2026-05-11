const { createApp } = Vue;

const defaultDate = () => new Date().toISOString().slice(0, 10);
const parseJsonText = (text, fallback, label) => {
  if (!text || !text.trim()) {
    return fallback;
  }
  try {
    return JSON.parse(text);
  } catch (error) {
    throw new Error(`${label} 不是合法 JSON`);
  }
};

createApp({
  data() {
    return {
      tabs: [
        { key: "register", label: "用户注册", desc: "创建新用户档案" },
        { key: "exercise", label: "运动记录", desc: "保存训练与恢复信息" },
        { key: "diet", label: "饮食记录", desc: "保存餐次与营养数据" },
        { key: "profile", label: "用户画像", desc: "查看和更新基础资料" },
        { key: "preferences", label: "用户偏好", desc: "维护偏好与限制条件" },
        { key: "chat", label: "Agent 对话", desc: "获取运动与饮食建议" }
      ],
      activeTab: "register",
      activeUserId: "",
      feedback: {
        type: "success",
        message: ""
      },
      loading: {
        register: false,
        exercise: false,
        diet: false,
        profile: false,
        profileSave: false,
        preferences: false,
        chat: false
      },
      registerForm: {
        tenant_id: "",
        username: "",
        age: 28,
        gender: "male",
        height: 175,
        weight: 70
      },
      registerGoalsText: "weight_loss,endurance",
      registerConstraintsText: '{"injury_history":[],"available_time":"weekday_evening"}',
      exerciseForm: {
        date: defaultDate(),
        exercise_type: 1,
        duration_minutes: 30,
        intensity: 5,
        calories_burned: 300,
        recovery_status: "normal",
        notes: ""
      },
      dietForm: {
        date: defaultDate(),
        meal_type: "lunch",
        calories: 550
      },
      dietFoodsText: "鸡胸肉|150g\n糙米|1碗\n西兰花|100g",
      dietNutrientsText: '{"protein":35,"carbs":48,"fat":12}',
      profile: {
        stats: {},
        recent_summary: {},
        exercise_preferences: {},
        diet_preferences: {}
      },
      profileForm: {
        username: "",
        age: null,
        gender: "male",
        height: null,
        weight: null
      },
      profileGoalsText: "",
      profileConstraintsText: "{}",
      preferencesForm: {
        exercise_preferences: "{}",
        diet_preferences: "{}",
        fitness_goals_text: "",
        constraints: "{}"
      },
      conversationId: (crypto.randomUUID && crypto.randomUUID()) || String(Date.now()),
      chatInput: "",
      chatMessages: [],
      exerciseOptions: [
        { value: 1, label: "running" },
        { value: 2, label: "swimming" },
        { value: 3, label: "hiking" },
        { value: 4, label: "cycling" },
        { value: 5, label: "strength_training" },
        { value: 6, label: "yoga" },
        { value: 7, label: "basketball" },
        { value: 8, label: "football" },
        { value: 9, label: "tennis" },
        { value: 10, label: "badminton" },
        { value: 11, label: "walking" },
        { value: 12, label: "skipping" },
        { value: 13, label: "dance" },
        { value: 99, label: "other" }
      ]
    };
  },
  computed: {
    currentTab() {
      return this.tabs.find((tab) => tab.key === this.activeTab) || this.tabs[0];
    }
  },
  mounted() {
    this.seedTenantId();
  },
  methods: {
    seedTenantId() {
      if (!this.registerForm.tenant_id) {
        this.registerForm.tenant_id = (crypto.randomUUID && crypto.randomUUID()) || `tenant-${Date.now()}`;
      }
    },
    setFeedback(message, type = "success") {
      this.feedback = { message, type };
      window.clearTimeout(this.feedbackTimer);
      this.feedbackTimer = window.setTimeout(() => {
        this.feedback.message = "";
      }, 5000);
    },
    ensureUserId() {
      if (!this.activeUserId) {
        throw new Error("请先注册用户或输入已有 user_id");
      }
    },
    splitGoals(text) {
      return text
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);
    },
    buildFoods() {
      const foods = this.dietFoodsText
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line) => {
          const [name, portion] = line.split("|").map((item) => item.trim());
          return { name, portion };
        });
      if (!foods.length || foods.some((item) => !item.name || !item.portion)) {
        throw new Error("食物列表格式应为 每行 食物名|份量");
      }
      return foods;
    },
    async apiRequest(path, options = {}) {
      const response = await fetch(path, {
        headers: {
          "Content-Type": "application/json",
          ...(options.headers || {})
        },
        ...options
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.detail || payload.message || "请求失败");
      }
      return payload;
    },
    async registerUser() {
      this.loading.register = true;
      try {
        const payload = {
          ...this.registerForm,
          fitness_goals: this.splitGoals(this.registerGoalsText),
          constraints: parseJsonText(this.registerConstraintsText, {}, "约束条件")
        };
        const result = await this.apiRequest("/api/v1/user/register", {
          method: "POST",
          body: JSON.stringify(payload)
        });
        this.activeUserId = result.user_id;
        this.activeTab = "profile";
        this.setFeedback(`注册成功，当前 user_id: ${result.user_id}`);
        await this.loadProfile();
      } catch (error) {
        this.setFeedback(error.message, "error");
      } finally {
        this.loading.register = false;
      }
    },
    async submitExercise() {
      this.loading.exercise = true;
      try {
        this.ensureUserId();
        const payload = {
          user_id: this.activeUserId,
          ...this.exerciseForm
        };
        await this.apiRequest("/api/v1/exercise/record", {
          method: "POST",
          body: JSON.stringify(payload)
        });
        this.setFeedback("运动记录已保存");
        await this.loadProfile();
      } catch (error) {
        this.setFeedback(error.message, "error");
      } finally {
        this.loading.exercise = false;
      }
    },
    async submitDiet() {
      this.loading.diet = true;
      try {
        this.ensureUserId();
        const payload = {
          user_id: this.activeUserId,
          ...this.dietForm,
          foods: this.buildFoods(),
          nutrients: parseJsonText(this.dietNutrientsText, {}, "营养信息")
        };
        await this.apiRequest("/api/v1/diet/record", {
          method: "POST",
          body: JSON.stringify(payload)
        });
        this.setFeedback("饮食记录已保存");
        await this.loadProfile();
      } catch (error) {
        this.setFeedback(error.message, "error");
      } finally {
        this.loading.diet = false;
      }
    },
    syncFormsFromProfile() {
      this.profileForm.username = this.profile.username || "";
      this.profileForm.age = this.profile.age ?? null;
      this.profileForm.gender = this.profile.gender || "male";
      this.profileForm.height = this.profile.height ?? null;
      this.profileForm.weight = this.profile.weight ?? null;
      this.profileGoalsText = (this.profile.fitness_goals || []).join(",");
      this.profileConstraintsText = JSON.stringify(this.profile.constraints || {}, null, 2);
      this.preferencesForm.exercise_preferences = JSON.stringify(this.profile.exercise_preferences || {}, null, 2);
      this.preferencesForm.diet_preferences = JSON.stringify(this.profile.diet_preferences || {}, null, 2);
      this.preferencesForm.fitness_goals_text = (this.profile.fitness_goals || []).join(",");
      this.preferencesForm.constraints = JSON.stringify(this.profile.constraints || {}, null, 2);
    },
    async loadProfile() {
      this.loading.profile = true;
      try {
        this.ensureUserId();
        const result = await this.apiRequest(`/api/v1/user/profile?user_id=${encodeURIComponent(this.activeUserId)}`);
        this.profile = result;
        this.syncFormsFromProfile();
        this.setFeedback("用户画像已刷新");
      } catch (error) {
        this.setFeedback(error.message, "error");
      } finally {
        this.loading.profile = false;
      }
    },
    async saveProfile() {
      this.loading.profileSave = true;
      try {
        this.ensureUserId();
        const payload = {
          ...this.profileForm,
          fitness_goals: this.splitGoals(this.profileGoalsText),
          constraints: parseJsonText(this.profileConstraintsText, {}, "画像约束条件")
        };
        await this.apiRequest(`/api/v1/user/profile?user_id=${encodeURIComponent(this.activeUserId)}`, {
          method: "PUT",
          body: JSON.stringify(payload)
        });
        this.setFeedback("用户画像已更新");
        await this.loadProfile();
      } catch (error) {
        this.setFeedback(error.message, "error");
      } finally {
        this.loading.profileSave = false;
      }
    },
    async savePreferences() {
      this.loading.preferences = true;
      try {
        this.ensureUserId();
        const payload = {
          exercise_preferences: parseJsonText(this.preferencesForm.exercise_preferences, {}, "运动偏好"),
          diet_preferences: parseJsonText(this.preferencesForm.diet_preferences, {}, "饮食偏好"),
          fitness_goals: this.splitGoals(this.preferencesForm.fitness_goals_text),
          constraints: parseJsonText(this.preferencesForm.constraints, {}, "限制条件")
        };
        await this.apiRequest(`/api/v1/user/preferences?user_id=${encodeURIComponent(this.activeUserId)}`, {
          method: "PUT",
          body: JSON.stringify(payload)
        });
        this.setFeedback("用户偏好已更新");
        await this.loadProfile();
      } catch (error) {
        this.setFeedback(error.message, "error");
      } finally {
        this.loading.preferences = false;
      }
    },
    startNewConversation() {
      this.conversationId = (crypto.randomUUID && crypto.randomUUID()) || `${Date.now()}`;
      this.chatMessages = [];
      this.setFeedback("已创建新的对话会话");
    },
    async sendChat() {
      this.loading.chat = true;
      try {
        this.ensureUserId();
        if (!this.chatInput) {
          throw new Error("请输入对话内容");
        }
        const message = this.chatInput;
        this.chatMessages.push({ role: "user", content: message });
        this.chatInput = "";
        const result = await this.apiRequest("/api/v1/chat", {
          method: "POST",
          body: JSON.stringify({
            user_id: this.activeUserId,
            message,
            conversation_id: this.conversationId
          })
        });
        const meta = JSON.stringify(
          {
            recommendations: result.recommendations || {},
            sources: result.sources || [],
            conversation_id: result.conversation_id
          },
          null,
          2
        );
        this.chatMessages.push({ role: "assistant", content: result.response, meta });
      } catch (error) {
        this.setFeedback(error.message, "error");
      } finally {
        this.loading.chat = false;
      }
    }
  }
}).mount("#app");
