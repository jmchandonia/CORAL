import {
  Component,
  OnInit,
  Input,
  Output,
  EventEmitter,
 } from '@angular/core';
import { QueryParam } from '../../../../shared/models/QueryBuilder';
import { QueryBuilderService } from '../../../../shared/services/query-builder.service';

@Component({
  selector: 'app-property-params',
  templateUrl: './property-params.component.html',
  styleUrls: ['./property-params.component.css'],
})
export class PropertyParamsComponent implements OnInit {

  @Output() removed: EventEmitter<any> = new EventEmitter();
  @Input() queryParam: QueryParam;
  @Input() dataType: string;

  propertyTypes: any[] = [];
  matchTypes: string[];
  selectedMatchType: string;
  selectedAttribute: string;

  constructor(
    private queryBuilder: QueryBuilderService
  ) {
  }

  ngOnInit() {
    this.selectedMatchType = this.queryParam.matchType;
    this.matchTypes = this.queryBuilder.getOperators();
    const attributes = this.queryBuilder.getAttributes(this.dataType);
    if (this.queryParam.attribute) {
      this.selectedAttribute = this.queryParam.attribute;
    }
    this.propertyTypes = [...attributes];
   }

  removeParam() {
    this.removed.emit();
  }

  setAttribute(event) {
    this.queryParam.attribute = event.name;
    this.queryParam.scalarType = event.scalar_type
  }

  setMatchType(event) {
    this.queryParam.matchType = event
  }

}
