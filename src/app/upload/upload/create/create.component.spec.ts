import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { FormsModule } from '@angular/forms';
import { Select2Module } from 'ng2-select2';
import { ModalModule } from 'ngx-bootstrap/modal';
import { BsDatepickerModule } from 'ngx-bootstrap/datepicker';
import { CreateComponent } from './create.component';
import { NgxSpinnerModule } from 'ngx-spinner';
import { HttpClientModule } from '@angular/common/http';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick, Term } from 'src/app/shared/models/brick';
import { Subject } from 'rxjs';

describe('CreateComponent', () => {
  let spectator: Spectator<CreateComponent>;

  const UploadServiceMock = {
    getBrickBuilder: () => new Brick(),
    getProcessOterms: () => new Subject<Term>(),
    getCampaignOterms: () => new Subject<Term>(),
    getPersonnelOterms: () => new Subject<Term>()
  };

  const createComponent = createComponentFactory({
    component: CreateComponent,
    imports: [
      FormsModule,
      Select2Module,
      ModalModule.forRoot(),
      BsDatepickerModule.forRoot(),
      NgxSpinnerModule,
      HttpClientModule
    ],
    providers: [
      mockProvider(UploadService, UploadServiceMock)
    ]
  });

  beforeEach(() => spectator = createComponent({
    props: {
      brick: new Brick()
    }
  }));

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});
