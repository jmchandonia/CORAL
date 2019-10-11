import { Component, OnInit, Input, Output, EventEmitter, ChangeDetectorRef } from '@angular/core';
import { Select2OptionData, } from 'ng2-select2';
import { QueryMatch, QueryParam } from '../../../shared/models/QueryBuilder';
import { NetworkService } from '../../../shared/services/network.service';
import { QueryBuilderService } from '../../../shared/services/query-builder.service';
import { HttpClient } from '@angular/common/http';
import * as $ from 'jquery';
import { Observable } from 'rxjs';
import { environment } from 'src/environments/environment';

@Component({
  selector: 'app-query-builder',
  templateUrl: './query-builder.component.html',
  styleUrls: ['./query-builder.component.css']
})
export class QueryBuilderComponent implements OnInit {

  public _queryMatch: QueryMatch = new QueryMatch();
  @Input() connection: string;
  @Input() title: string;
  @Output() create: EventEmitter<QueryMatch> = new EventEmitter();
  @Input() operators = [];
  @Input() set queryMatch(value: QueryMatch) {
    this._queryMatch = value;
    if (value && value.dataType) {
      this.selectedDataType = value.dataType;
      this.dataTypeList.push({id : '0', text: value.dataType});
    }
  }
  get queryMatch() {
    return this._queryMatch;
  }
  private ajaxOptions: Select2AjaxOptions;
  public selectedAttributes: any;
  dataModels: any;
  dataTypes: any;
  selectedDataType: string;

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
    private network: NetworkService,
    private http: HttpClient,
    private chRef: ChangeDetectorRef
  ) { }

  ngOnInit() {

    if (!this.queryMatch) {
      this.queryMatch = new QueryMatch();
    }

    this.http.get(`${environment.baseURL}/data_models`)
      .subscribe((data: any) => {
        this.dataModels = data.results;
      });

    this.ajaxOptions = {
      url: `${environment.baseURL}/data_types`,
      dataType: 'json',
      delay: 250,
      cache: false,
      processResults: (data: any) => {
        this.dataTypes = data.results;
        return {
          results: $.map(data.results, (obj, idx) => {
            return {id: idx.toString(), text: obj.dataType};
          }),
        };
      },
    };
    this.options.ajax = this.ajaxOptions;
}

  updateObjectDataModel(event) {
    const selected = this.dataTypes[parseInt(event.value, 10)];
    const selectedModel = this.dataModels[selected.dataModel];
    this.selectedAttributes = selectedModel.properties;
    Object.keys(selected).forEach(key => {
      this.queryMatch[key] = selected[key];
    });
    this.queryMatch.params = [];
    this.updateQueryMatch();
  }

  updatePropertyParam(index, event) {
    this.queryMatch.params[index][event.key] = event.value.data[0].text;
    this.updateQueryMatch();
  }

  removePropertyParam(param) {
    this.queryMatch.params = this.queryMatch.params.filter(p => p !== param);
    this.updateQueryMatch();
  }

  addPropertyParam(param) {
    this.queryMatch.params.push(param);
    this.updateQueryMatch();
  }

  updateQueryMatch() {
    this.queryBuilder.updateQueryMatch(this.connection, this.queryMatch);
  }

}
