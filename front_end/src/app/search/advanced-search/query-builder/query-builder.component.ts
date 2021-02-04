import { Component, OnInit, OnDestroy, Input, Output, EventEmitter } from '@angular/core';
import { QueryMatch, QueryParam, QueryMatchData } from '../../../shared/models/QueryBuilder';
import { QueryBuilderService } from '../../../shared/services/query-builder.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-query-builder',
  templateUrl: './query-builder.component.html',
  styleUrls: ['./query-builder.component.css']
})
export class QueryBuilderComponent implements OnInit, OnDestroy {

  @Input() connection: string;
  @Input() title: string;
  @Output() create: EventEmitter<QueryMatch> = new EventEmitter();
  @Input() queryMatch: QueryMatch;
  public selectedAttributes: any;
  dataModels: any;
  dataTypes: any;
  operators: string[] = [];
  selectedDataType: QueryMatchData;
  dataTypeSub = new Subscription();

  constructor(
    private queryBuilder: QueryBuilderService,
  ) { }

  ngOnInit() {
    const loadedDataTypes = this.queryBuilder.getLoadedDataTypes();
    if (loadedDataTypes) {
      this.dataTypes = loadedDataTypes;
      if (this.queryMatch && !this.queryMatch.isEmpty) {
        this.selectedDataType = this.queryMatch.data;
      }
    } else {
      this.dataTypeSub = this.queryBuilder.getDataTypes()
      .subscribe(dataTypes => {
        this.dataTypes = dataTypes;
      });
    }
}

  ngOnDestroy() {
    if (this.dataTypeSub) {
      this.dataTypeSub.unsubscribe();
    }
  }

  updateQueryMatch(event: QueryMatchData) {
    this.selectedDataType = event;
    if (!this.queryMatch) { 
      this.queryMatch = new QueryMatch(event);
      this.create.emit(this.queryMatch);
    }
    Object.keys(event).forEach(key => {
      this.queryMatch[key] = event[key];
    })
  }

  handleClear() {
    delete this.queryMatch;
  }

  removePropertyParam(param) {
    this.queryMatch.params = this.queryMatch.params.filter(p => p !== param);
  }

  addPropertyParam() {
    this.queryMatch.params.push(new QueryParam());
  }

  getImgSource(item: QueryMatchData) {
    return item.category === 'DDT_'
      ? './assets/Brick.png'
      : './assets/Sample.png';
  }

}
