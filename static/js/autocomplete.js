/**
 * 自動補全與標籤功能模組
 * 提供公司代號/名稱的自動補全與標籤管理功能
 */
export class AutocompleteService {
  constructor() {
    this.inputField = null;
    this.autocompleteList = null;
    this.selectedCompaniesContainer = null;
    this.hiddenInput = null;
    this.selectedCompanies = [];
  }

  /**
   * 初始化自動補全服務
   */
  init() {
    // 檢查 DOM 元素是否存在
    this.inputField = document.getElementById("company-ids");
    this.autocompleteList = document.getElementById("autocomplete-results");
    this.selectedCompaniesContainer = document.getElementById("selected-companies");
    this.hiddenInput = document.getElementById("company-ids-hidden");

    if (!this.inputField || !this.autocompleteList || !this.selectedCompaniesContainer || !this.hiddenInput) {
      console.error("無法找到必要的 DOM 元素");
      return;
    }

    // 檢查全局股票列表是否存在
    if (!window.STOCK_LIST || !Array.isArray(window.STOCK_LIST)) {
      console.error("STOCK_LIST 未正確載入！");
      return;
    }

    // 監聽輸入事件，進行模糊搜尋
    this.inputField.addEventListener("input", this.handleInput.bind(this));

    // 點擊外部時，清除自動補全選單
    document.addEventListener("click", (event) => {
      if (!this.inputField.contains(event.target) && !this.autocompleteList.contains(event.target)) {
        this.autocompleteList.innerHTML = "";
      }
    });
  }

  /**
   * 處理輸入事件
   * @param {Event} event - 輸入事件
   */
  handleInput(event) {
    let query = event.target.value.trim();
    this.autocompleteList.innerHTML = "";
    
    if (query === "") return;

    // 篩選符合條件的公司
    let matches = window.STOCK_LIST.filter(
      (company) => company.code.includes(query) || company.name.includes(query)
    );

    // 創建自動補全項目
    matches.forEach((company) => {
      let item = document.createElement("div");
      item.classList.add("autocomplete-item");
      item.textContent = `${company.code} ${company.name}`;
      item.dataset.code = company.code;

      item.addEventListener("click", () => {
        this.addCompanyTag(company);
        // 清空可見的輸入框
        this.inputField.value = "";
        this.autocompleteList.innerHTML = "";
      });

      this.autocompleteList.appendChild(item);
    });
  }

  /**
   * 加入公司標籤
   * @param {Object} company - 公司資訊 {code: string, name: string}
   */
  addCompanyTag(company) {
    // 避免重複添加
    if (this.selectedCompanies.includes(company.code)) return;
    this.selectedCompanies.push(company.code);
    
    // 創建標籤元素
    let tag = document.createElement("span");
    tag.classList.add("company-tag");
    
    // 創建標籤文字元素
    let tagText = document.createElement("span");
    tagText.textContent = `${company.code} ${company.name}`;
    
    // 創建移除按鈕 (iPhone 風格的小叉)
    let removeButton = document.createElement("span");
    removeButton.classList.add("remove-btn");
    removeButton.innerHTML = "×";
    
    // 點擊移除按鈕可移除標籤
    removeButton.addEventListener("click", (event) => {
      event.stopPropagation(); // 阻止事件冒泡到標籤元素
      this.selectedCompanies = this.selectedCompanies.filter(
        (code) => code !== company.code
      );
      tag.remove();
      this.updateHiddenInput();
    });
    
    // 將文字和移除按鈕加入標籤元素
    tag.appendChild(tagText);
    tag.appendChild(removeButton);
    tag.dataset.code = company.code;
    
    this.selectedCompaniesContainer.appendChild(tag);
    this.updateHiddenInput();
  }

  /**
   * 更新隱藏欄位的值
   */
  updateHiddenInput() {
    this.hiddenInput.value = this.selectedCompanies.join(",");
    console.log("公司", this.hiddenInput.value);
  }

  /**
   * 根據公司ID字符串更新標籤
   * @param {string} companyIdsStr - 逗號分隔的公司ID字符串
   */
  updateCompanyTags(companyIdsStr) {
    if (!window.STOCK_LIST || !Array.isArray(window.STOCK_LIST)) {
      return;
    }

    // 清空現有標籤
    if (this.selectedCompaniesContainer) {
      this.selectedCompaniesContainer.innerHTML = '';
    }

    // 解析公司代號
    const companyIds = companyIdsStr.split(',');
    
    // 重設選中公司列表
    this.selectedCompanies = [];
    
    // 重新建立標籤
    companyIds.forEach(companyId => {
      const trimmedId = companyId.trim();
      if (trimmedId) {
        this.selectedCompanies.push(trimmedId);
        
        // 找到對應的公司資訊
        const companyInfo = window.STOCK_LIST.find(company => company.code === trimmedId);
        
        if (companyInfo && this.selectedCompaniesContainer) {
          this.addCompanyTag(companyInfo);
        }
      }
    });
  }

  /**
   * 清除所有標籤
   */
  clearTags() {
    if (this.selectedCompaniesContainer) {
      this.selectedCompaniesContainer.innerHTML = '';
    }
    this.selectedCompanies = [];
    this.updateHiddenInput();
  }
}