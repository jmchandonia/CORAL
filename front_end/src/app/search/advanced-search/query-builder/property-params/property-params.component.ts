import {
  Component,
  OnInit,
  Input,
  Output,
  EventEmitter,
 } from '@angular/core';
import { QueryParam } from '../../../../shared/models/QueryBuilder';
import { QueryBuilderService } from '../../../../shared/services/query-builder.service';
import { BsDatepickerConfig } from 'ngx-bootstrap/datepicker';

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

  datepickerConfig: Partial<BsDatepickerConfig> = {
    containerClass: 'theme-dark-blue',
    useUtc: true
  };

  ngOnInit() {
    this.selectedMatchType = this.queryParam.matchType;
    const attributes = this.queryBuilder.getAttributes(this.dataType);
    if (this.queryParam.attribute) {
      this.selectedAttribute = this.queryParam.attribute;
      this.setOperators();
    }
    this.propertyTypes = [...attributes];
   }

  removeParam() {
    this.removed.emit();
  }

  setAttribute(event) {
    this.queryParam.attribute = event.name;
    this.queryParam.scalarType = event.scalar_type
    this.setOperators();
  }

  setOperators() {
    this.matchTypes = this.queryBuilder.getOperators(this.queryParam);
  }

  setMatchType(event) {
    this.queryParam.matchType = event
  }

  handleDateSelected(event: Date) {
    if (!event) return;
    this.queryParam.keyword = event.toISOString().split('T')[0];
  }

}
