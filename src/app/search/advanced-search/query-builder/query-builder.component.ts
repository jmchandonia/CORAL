import { Component, OnInit, OnDestroy, Input, Output, EventEmitter, ChangeDetectorRef } from '@angular/core';
import { Select2OptionData, } from 'ng2-select2';
import { QueryMatch, QueryParam } from '../../../shared/models/QueryBuilder';
import { NetworkService } from '../../../shared/services/network.service';
import { QueryBuilderService } from '../../../shared/services/query-builder.service';
import { HttpClient } from '@angular/common/http';
import * as $ from 'jquery';
import { Subscription } from 'rxjs';
import { environment } from 'src/environments/environment';

@Component({
  selector: 'app-query-builder',
  templateUrl: './query-builder.component.html',
  styleUrls: ['./query-builder.component.css']
})
export class QueryBuilderComponent implements OnInit, OnDestroy {

  public _queryMatch: QueryMatch = new QueryMatch();
  @Input() connection: string;
  @Input() title: string;
  @Output() create: EventEmitter<QueryMatch> = new EventEmitter();
  @Input() set dataProps(data: any) {
    this.dataModels = data.dataModels;
    // this.dataTypes = data.dataTypes;
    this.operators = data.operators;
  }
  @Input() set queryMatch(value: QueryMatch) {
    this._queryMatch = value;
  }
  get queryMatch() {
    return this._queryMatch;
  }
  private ajaxOptions: Select2AjaxOptions;
  public selectedAttributes: any;
  dataModels: any;
  dataTypes: any;
  operators: string[] = [];
  selectedDataType: string;
  dataTypeSub = new Subscription();

  options: Select2Options = {
    width: '100%',
    containerCssClass: 'select2-custom-container',
    placeholder: 'Select A Data Type',
    templateResult: state => {
      if (!state.id) { return state; }
      const obj = this.dataTypes[parseInt(state.id, 10)];
      return `<span><img class="icon" src="./assets/${obj.category === 'DDT_' ? 'Brick' : 'Sample'}.png" />${state.text}</span>`;
    },
    escapeMarkup: m => m
  };

  dataTypeList: Array<Select2OptionData> = [
    {
      id: '',
      text: ''
    },
  ];

  constructor(
    private queryBuilder: QueryBuilderService,
    private http: HttpClient,
    private chRef: ChangeDetectorRef
  ) { }

  ngOnInit() {
    // TODO: make all querymatches initialize right away

    const loadedDataTypes = this.queryBuilder.getLoadedDataTypes();
    if (loadedDataTypes) {
      this.populateDataTypes(loadedDataTypes);
      if (this.queryMatch && this.queryMatch.dataType) {
        this.selectedDataType = this.dataTypeList.find(item => item.text === this.queryMatch.dataType).id;
      }
    } else {
      this.dataTypeSub = this.queryBuilder.getDataTypes()
      .subscribe(dataTypes => {
        this.populateDataTypes(dataTypes);
      });
    }

    if (!this.queryMatch) {
      this.queryMatch = new QueryMatch();
    }
}

  populateDataTypes(dataTypes) {
    this.dataTypes = dataTypes;
    this.dataTypeList = [{id: '', text: ''}, ...this.dataTypes.map((type, idx) => {
      return {id: idx.toString(), text: type.dataType};
    })];
  }

  ngOnDestroy() {
    if (this.dataTypeSub) {
      this.dataTypeSub.unsubscribe();
    }
  }

  updateObjectDataModel(event) {
    // const selected = this.dataTypes[parseInt(event.value, 10)];
    // const selectedModel = this.dataModels[selected.dataModel];
    // this.selectedAttributes = selectedModel.properties;
    // Object.keys(selected).forEach(key => {
    //   this.queryMatch[key] = selected[key];
    // });
    if (this.dataTypes && event.value.length) {
      const selected = this.dataTypes[parseInt(event.value, 10)];
      Object.keys(selected).forEach(key => {
      this.queryMatch[key] = selected[key];
      });
      // this.selectedDataType = event.data[0].text;
    }
  }

  updatePropertyParam(index, event) {
    this.queryMatch.params[index][event.key] = event.value.data[0].text;
  }

  removePropertyParam(param) {
    this.queryMatch.params = this.queryMatch.params.filter(p => p !== param);
  }

  addPropertyParam() {
    this.queryMatch.params.push(new QueryParam());
  }

}
