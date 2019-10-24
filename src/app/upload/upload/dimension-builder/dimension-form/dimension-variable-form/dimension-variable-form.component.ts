import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { BrickDimension, DimensionVariable, Term, Context } from 'src/app/shared/models/brick';
import { Select2OptionData } from 'ng2-select2';
import { UploadService } from 'src/app/shared/services/upload.service';

@Component({
  selector: 'app-dimension-variable-form',
  templateUrl: './dimension-variable-form.component.html',
  styleUrls: ['./dimension-variable-form.component.css']
})
export class DimensionVariableFormComponent implements OnInit {

  // @Input() dimVar: DimensionVariable;
  @Input() set dimVar(d: DimensionVariable) {
    this._dimVar = d;
    if (d.type) {
      // this.typeData = [d.type];
      if (d.context.length) {
        this.typeData = [this.setContextLabel(d.type, d.context[0])];
      } else {
        this.typeData = [d.type];
      }
      this.selectedType = d.type.id;
    }

    if (d.units) {
      this.unitsData = [d.units];
      this.selectedUnits = d.units.id;
    }
  }

  get dimVar() {
    return this._dimVar;
  }

  typeData: Array<Select2OptionData> = [];
  unitsData: Array<Select2OptionData> = [];
  selectedType: string;
  selectedUnits: string;

  private _dimVar: DimensionVariable;

  @Output() deleted: EventEmitter<DimensionVariable> = new EventEmitter();

  typeOptions: Select2Options = {
    width: '100%',
    containerCssClass: 'select2-custom-container',
    query: (options: Select2QueryOptions) => {
      const term = options.term;
      if (!term || term.length < 3) {
        options.callback({results: []});
      } else {
        this.uploadService.searchOntTerms(term)
          .subscribe((data: any) => {
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
        this.uploadService.searchOntUnits(term)
          .subscribe((data: any) => {
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

  setContextLabel(type: Term, context: Context) {
    const label = type;
    const { property, value, units } = context;
    label.text += `, ${property.text}=${value.text}`;
    if (units) {
      label.text += ` (${units.text})`;
    }
    return label;
  }

  delete() {
    this.deleted.emit(this.dimVar);
  }

  setDimVarType(event) {
    const term = event.data[0];
    this.dimVar.type = new Term(term.id, term.text);
  }

  setDimVarUnits(event) {
    const term = event.data[0];
    this.dimVar.units = new Term(term.id, term.text);
  }

}
