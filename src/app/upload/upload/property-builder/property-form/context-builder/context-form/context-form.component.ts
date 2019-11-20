import { Component, OnInit, Input, Output, EventEmitter, OnDestroy } from '@angular/core';
import { Context, Term } from 'src/app/shared/models/brick';
import { UploadService } from 'src/app/shared/services/upload.service';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';
import { Select2OptionData } from 'ng2-select2';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-context-form',
  templateUrl: './context-form.component.html',
  styleUrls: ['./context-form.component.css']
})
export class ContextFormComponent implements OnInit, OnDestroy {


  private _context: Context;

  @Input() set context(c: Context) {
    this._context = c;

    this.typesSelect2 = c.type ? [c.type] : [];
    this.unitsSelect2 = c.units ? [c.units] : [{id: '', text: ''}];
    this.valuesSelect2 = c.value && c.scalarType === 'oterm_ref'
      ? [c.value] as Select2OptionData[]
      : [{id: '', text: ''}];

    if (c.type) {
      this.typeItem = c.type.id;
    }
    if (c.units) {
      this.unitsItem = c.units.id;
    }
    if (c.value && c.scalarType === 'oterm_ref') {
      this.valueItem = (c.value as Term).id;
    }

    if (this.context.microType) {
      this.getUnits();
    }
  }

  get context() { return this._context; }

  @Output() resetContext: EventEmitter<Context> = new EventEmitter();
  @Output() deleted: EventEmitter<any> = new EventEmitter();
  errorSub: Subscription;

  typesOptions: Select2Options = {
    width: '100%',
    containerCssClass: 'select2-custom-container',
    query: (options: Select2QueryOptions) => {
      const term = options.term;
      if (!term || term.length < 3) {
        options.callback({results: []});
      } else {
        this.uploadService.searchPropertyMicroTypes(term).subscribe((data: any) => {
          options.callback({results: data.results as Select2OptionData});
        });
      }
    }
   };

   valuesOptions: Select2Options = {
     width: '100%',
     containerCssClass: 'select2-custom-container',
     query: (options: Select2QueryOptions) => {
       const term = options.term;
       if (!term || term.length < 3) {
         options.callback({results: []});
       } else {
         this.uploadService.searchOntPropertyValues(term, this.context.microType) // ADD POST DATA
          .subscribe((data: any) => {
            options.callback({results: data.results as Select2OptionData});
          });
       }
     }
   };

  unitsOptions: Select2Options = {
    width: '100%',
    containerCssClass: 'select2-custom-container',
   };

  public typesSelect2: Select2OptionData[];
  public unitsSelect2: Select2OptionData[];
  public valuesSelect2: Select2OptionData[];

  typeItem: string;
  unitsItem: string;
  valueItem: string;
  error = false;

  constructor(
    private uploadService: UploadService,
    private validator: UploadValidationService
  ) { }

  ngOnInit() {
    this.errorSub = this.validator.getContextValidationErrors()
      .subscribe(error => this.error = error);
  }

  ngOnDestroy() {
    if (this.errorSub) {
      this.errorSub.unsubscribe();
    }
  }

  getUnits() {
    this.uploadService.searchOntPropertyUnits(this.context.microType)
    .subscribe(data => {
      if (!data.results.length) {
        this.context.units = null as Term;
      } else {
        if (this.context.units === null) {
          this.context.units = undefined;
        }
        this.unitsSelect2 = [...this.unitsSelect2, ...data.results];
      }
  });
  }

  setContextType(event) {
    const item = event.data[0];
    this.context.type = item;

    // clear reset entire property object to clear other select 2 dropdowns
    if (this.context.value || this.context.units) {
      const resetProperty = new Context(
        this.context.required,
        item
        // this.property.type,
        // this.property.microType
      );
      // emit new typed property to replace old one in parent component array reference
      this.resetContext.emit(resetProperty);
    } else {
      this.getUnits();
      // this.validate();
    }
  }

  setValue(event) {
    const item = event.data[0];
    this.context.value = new Term(item.id, item.text);
    // this.validate();
  }

  setUnits(event) {
    if (event.value.length) {
      const item = event.data[0];
      this.context.units = new Term(item.id, item.text);
      // this.validate();
    }
  }

  onDelete() {
    this.deleted.emit();
  }

}
