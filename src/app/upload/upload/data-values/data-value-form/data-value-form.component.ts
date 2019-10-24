import { Component, OnInit, Input, EventEmitter, Output } from '@angular/core';
import { DataValue, Term } from 'src/app/shared/models/brick';
import { Select2OptionData } from 'ng2-select2';
import { UploadService } from 'src/app/shared/services/upload.service';

@Component({
  selector: 'app-data-value-form',
  templateUrl: './data-value-form.component.html',
  styleUrls: ['./data-value-form.component.css']
})
export class DataValueFormComponent implements OnInit {

  @Input() set dataValue(d: DataValue) {
    this._dataValue = d;
    console.log('DATA VALUE', this.dataValue);

    if (d.scalarType) {
      this.scalarValues = [d.scalarType];
      this.scalarValuesItem = d.scalarType.id;
    }

    if (d.type) {
      this.typeValues = [d.type];
      this.typeValuesItem = d.type.id;
    }

    if (d.units) {
      this.unitsValues = [d.units];
      this.unitsItem = d.units.id;
    }
  }

  get dataValue() { return this._dataValue; }

  @Output() removed: EventEmitter<any> = new EventEmitter();

  // tslint:disable-next-line:variable-name
  private _dataValue: DataValue;

  scalarValues: Array<Select2OptionData> = [{id: '', text: ''}];
  typeValues: Array<Select2OptionData> = [{id: '', text: ''}];
  unitsValues: Array<Select2OptionData> = [{id: '', text: ''}];

  scalarValuesItem: string;
  typeValuesItem: string;
  unitsItem: string;

  scalarOptions: Select2Options = {
    width: '100%',
    containerCssClass: 'select2-custom-container',
    query: (options: Select2QueryOptions) => {
      const term = options.term;
      if (!term || term.length < 3) {
        options.callback({results: []});
      } else {
        this.uploadService.searchOntTerms(term).subscribe((data: any) => {
          options.callback({results: data.results as Select2OptionData});
        });
      }
    }
   };

   unitsOptions: Select2Options = {
    width: '100%',
    containerCssClass: 'select2-custom-container',
    query: (options: Select2QueryOptions) => {
      const term = options.term;
      if (!term || term.length < 3) {
        options.callback({results: []});
      } else {
        this.uploadService.searchOntUnits(term).subscribe((data: any) => {
          options.callback({results: data.results as Select2OptionData});
        });
      }
    }
   };

   typesOptions: Select2Options = {
    width: '100%',
    containerCssClass: 'select2-custom-container',
    query: (options: Select2QueryOptions) => {
      const term = options.term;
      if (!term || term.length < 3) {
        options.callback({results: []});
      } else {
        this.uploadService.searchOntTerms(term).subscribe((data: any) => {
          options.callback({results: data.results as Select2OptionData});
        });
      }
    }
   };

  constructor(
    private uploadService: UploadService
  ) { }

  ngOnInit() {
  }

  onDelete() {
    this.removed.emit();
  }

  updateType(event) {
    const type = event.data[0];
    this.dataValue.type = new Term(type.id, type.text);
  }

  updateScalarType(event) {
    const scalarType = event.data[0];
    this.dataValue.scalarType = new Term(scalarType.id, scalarType.text);
  }

  updateUnits(event) {
    const units = event.data[0];
    this.dataValue.units = new Term(units.id, units.text);
  }

}
